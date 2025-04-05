#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys

def get_public_ip():
    """Test public IP address retrieval"""
    ip_services = [
        'https://ifconfig.me/ip',
        'https://api.ip.sb/ip',
        'https://ipinfo.io/ip'
    ]
    
    print("Testing public IP address retrieval...")
    
    for i, service in enumerate(ip_services, 1):
        try:
            print(f"Trying service {i}: {service}")
            response = requests.get(service, timeout=10)
            if response.status_code == 200:
                ip = response.text.strip()
                print(f"Successfully obtained public IP: {ip}")
                return ip
        except Exception as e:
            print(f"Failed to get IP from {service}: {e}")
            continue
            
    print("Unable to obtain public IP address, please check your network connection")
    return None

if __name__ == "__main__":
    try:
        ip = get_public_ip()
        if ip:
            print("\nTest successful! Your public IP address is:", ip)
            print("You can now proceed with configuring the Cloudflare DDNS client")
        else:
            print("\nTest failed! Unable to obtain public IP address")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")
        sys.exit(1)