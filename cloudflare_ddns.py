#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import logging
import requests
import argparse
from datetime import datetime
from configparser import ConfigParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cloudflare_ddns.log')
    ]
)
logger = logging.getLogger(__name__)

class CloudflareDDNS:
    def __init__(self, config_file='config.ini'):
        """Initialize Cloudflare DDNS client"""
        self.config_file = config_file
        self.config = self._load_config()
        self.ip_cache_file = 'ip_cache.json'
        self.domains_config = self._parse_domains_config()
        self.cached_ips = self._load_cached_ips()
        
    def _load_config(self):
        """Load configuration file"""
        if not os.path.exists(self.config_file):
            logger.error(f"Configuration file {self.config_file} does not exist")
            sys.exit(1)
            
        config = ConfigParser()
        config.read(self.config_file, encoding='utf-8')
        
        # Validate global configuration
        if not config.has_section('cloudflare'):
            logger.error("Configuration file missing [cloudflare] section")
            sys.exit(1)
            
        # Support both API Token and Global API Key
        if not config.has_option('cloudflare', 'api_token') and not config.has_option('cloudflare', 'api_key'):
            logger.error("Configuration missing authentication info, requires api_token or api_key")
            sys.exit(1)
            
        # Validate domain configurations
        domain_sections = [s for s in config.sections() if s.startswith('domain:')]
        if not domain_sections:
            # Check for legacy single domain configuration
            if all(config.has_option('cloudflare', field) for field in ['zone_id', 'domain']):
                logger.warning("Using legacy single domain configuration format, consider updating to multi-domain format")
            else:
                logger.error("No domain configurations found in config file")
                sys.exit(1)
                
        return config
    
    def _parse_domains_config(self):
        """Parse domain configurations"""
        domains_config = []
        
        # Get authentication info
        self.auth = {}
        if self.config.has_option('cloudflare', 'api_token'):
            self.auth['api_token'] = self.config.get('cloudflare', 'api_token')
        else:
            self.auth['api_key'] = self.config.get('cloudflare', 'api_key')
            self.auth['email'] = self.config.get('cloudflare', 'email')
        
        # Check for domain configuration sections
        domain_sections = [s for s in self.config.sections() if s.startswith('domain:')]
        
        if domain_sections:
            # New multi-domain configuration
            for section in domain_sections:
                domain_name = section[7:]  # Remove 'domain:' prefix
                
                # Validate required fields
                required_fields = ['zone_id', 'record_type']
                missing_fields = [field for field in required_fields
                                 if not self.config.has_option(section, field)]
                
                if missing_fields:
                    logger.error(f"Domain {domain_name} configuration missing required fields: {', '.join(missing_fields)}")
                    continue
                
                domains_config.append({
                    'name': domain_name,
                    'zone_id': self.config.get(section, 'zone_id'),
                    'record_type': self.config.get(section, 'record_type', fallback='A'),
                    'ttl': self.config.getint(section, 'ttl', fallback=1),
                    'proxied': self.config.getboolean(section, 'proxied', fallback=False)
                })
        else:
            # Legacy single domain configuration
            if self.config.has_option('cloudflare', 'domain'):
                domain_name = self.config.get('cloudflare', 'domain')
                
                # Validate required fields
                required_fields = ['zone_id']
                missing_fields = [field for field in required_fields
                                 if not self.config.has_option('cloudflare', field)]
                
                if missing_fields:
                    logger.error(f"Domain {domain_name} configuration missing required fields: {', '.join(missing_fields)}")
                    return domains_config
                
                domains_config.append({
                    'name': domain_name,
                    'zone_id': self.config.get('cloudflare', 'zone_id'),
                    'record_type': self.config.get('cloudflare', 'record_type', fallback='A'),
                    'ttl': self.config.getint('cloudflare', 'ttl', fallback=1),
                    'proxied': self.config.getboolean('cloudflare', 'proxied', fallback=False)
                })
        
        logger.info(f"Loaded {len(domains_config)} domain configurations")
        return domains_config
    
    def _get_auth_headers(self):
        """Get authentication headers"""
        if 'api_token' in self.auth:
            return {
                'Authorization': f'Bearer {self.auth["api_token"]}',
                'Content-Type': 'application/json'
            }
        else:
            return {
                'X-Auth-Email': self.auth['email'],
                'X-Auth-Key': self.auth['api_key'],
                'Content-Type': 'application/json'
            }
    
    def _load_cached_ips(self):
        """Load cached IP addresses"""
        cached_ips = {}
        
        if not os.path.exists(self.ip_cache_file):
            return cached_ips
            
        try:
            with open(self.ip_cache_file, 'r') as f:
                cache = json.load(f)
                
                # Support legacy cache format
                if isinstance(cache, dict) and 'ip' in cache:
                    # Legacy single IP cache
                    for domain in self.domains_config:
                        cached_ips[domain['name']] = cache['ip']
                elif isinstance(cache, dict):
                    # New multi-domain cache
                    cached_ips = cache
                    
        except Exception as e:
            logger.warning(f"Failed to read IP cache file: {e}")
            
        return cached_ips
    
    def _save_cached_ips(self, ips_dict):
        """Save IP addresses to cache file"""
        try:
            with open(self.ip_cache_file, 'w') as f:
                json.dump({
                    **ips_dict,
                    'updated_at': datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save IP cache file: {e}")
    
    def get_public_ip(self):
        """Get public IP address"""
        ip_services = [
            'https://ifconfig.me/ip',
            'https://api.ip.sb/ip',
            'https://ipinfo.io/ip'
        ]
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=10)
                if response.status_code == 200:
                    ip = response.text.strip()
                    logger.info(f"Successfully obtained public IP: {ip}")
                    return ip
            except Exception as e:
                logger.warning(f"Failed to get IP from {service}: {e}")
                continue
                
        logger.error("Unable to obtain public IP address")
        return None
    
    def get_dns_record(self, domain_config):
        """Get current DNS record"""
        headers = self._get_auth_headers()
        zone_id = domain_config['zone_id']
        domain = domain_config['name']
        record_type = domain_config['record_type']
        
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        params = {
            'name': domain,
            'type': record_type
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['success'] and len(data['result']) > 0:
                record = data['result'][0]
                logger.info(f"Successfully retrieved DNS record: {record['name']} ({record['id']})")
                return record
            else:
                logger.error(f"No DNS record found for domain {domain}")
                return None
        except Exception as e:
            logger.error(f"Failed to get DNS record: {e}")
            return None
    
    def update_dns_record(self, domain_config, record_id, ip):
        """Update DNS record"""
        headers = self._get_auth_headers()
        zone_id = domain_config['zone_id']
        domain = domain_config['name']
        record_type = domain_config['record_type']
        ttl = domain_config['ttl']
        proxied = domain_config['proxied']
        
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        data = {
            'type': record_type,
            'name': domain,
            'content': ip,
            'ttl': ttl,
            'proxied': proxied
        }
        
        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result['success']:
                logger.info(f"Successfully updated DNS record for {domain}")
                return True
            else:
                logger.error(f"Failed to update DNS record for {domain}: {result['errors']}")
                return False
        except Exception as e:
            logger.error(f"Failed to update DNS record: {e}")
            return False
    
    def create_dns_record(self, domain_config, ip):
        """Create new DNS record"""
        headers = self._get_auth_headers()
        zone_id = domain_config['zone_id']
        domain = domain_config['name']
        record_type = domain_config['record_type']
        ttl = domain_config['ttl']
        proxied = domain_config['proxied']
        
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        data = {
            'type': record_type,
            'name': domain,
            'content': ip,
            'ttl': ttl,
            'proxied': proxied
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result['success']:
                logger.info(f"Successfully created DNS record for {domain}")
                return True
            else:
                logger.error(f"Failed to create DNS record for {domain}: {result['errors']}")
                return False
        except Exception as e:
            logger.error(f"Failed to create DNS record: {e}")
            return False
    
    def update_domain(self, domain_config, current_ip):
        """Update DNS record for a domain"""
        domain = domain_config['name']
        cached_ip = self.cached_ips.get(domain)
        
        if cached_ip == current_ip:
            logger.info(f"IP address unchanged for {domain}: {current_ip}")
            return True
            
        record = self.get_dns_record(domain_config)
        if record:
            if record['content'] == current_ip:
                logger.info(f"DNS record already up to date for {domain}")
                self.cached_ips[domain] = current_ip
                return True
                
            if self.update_dns_record(domain_config, record['id'], current_ip):
                self.cached_ips[domain] = current_ip
                return True
        else:
            if self.create_dns_record(domain_config, current_ip):
                self.cached_ips[domain] = current_ip
                return True
                
        return False
    
    def update(self):
        """Update all configured domains"""
        current_ip = self.get_public_ip()
        if not current_ip:
            return False
            
        success = True
        for domain_config in self.domains_config:
            if not self.update_domain(domain_config, current_ip):
                success = False
                
        if success:
            self._save_cached_ips(self.cached_ips)
            
        return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Cloudflare DDNS Client')
    parser.add_argument('-c', '--config', default='config.ini',
                      help='Path to configuration file')
    parser.add_argument('-i', '--interval', type=int,
                      help='Update interval in seconds')
    args = parser.parse_args()
    
    client = CloudflareDDNS(args.config)
    
    if args.interval:
        logger.info(f"Running in daemon mode, update interval: {args.interval} seconds")
        while True:
            client.update()
            time.sleep(args.interval)
    else:
        client.update()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)