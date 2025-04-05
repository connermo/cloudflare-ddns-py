# Cloudflare DDNS Client

A simple Python script that automatically updates Cloudflare DNS records with your current public IP address, providing Dynamic DNS (DDNS) functionality.

## Features

- Support for multiple domain configurations
- Automatic public IP address detection (using multiple IP lookup services for reliability)
- Automatic Cloudflare DNS record updates
- Configurable update intervals
- IP address caching to minimize API calls
- Detailed logging
- Docker support

## Installation and Usage

### Method 1: Using Docker (Recommended)

1. Copy the configuration template:
```bash
cp config.ini.example config.ini
```

2. Edit `config.ini` file

3. Start the container (either way):

#### Using docker-compose (Recommended)
```bash
docker-compose up -d
```

#### Using Docker Command
```bash
docker run -d \
  --name cloudflare-ddns \
  -v $(pwd)/config.ini:/config/config.ini:ro \
  -e UPDATE_INTERVAL=300 \
  --restart unless-stopped \
  connermo/cloudflare-ddns-py:latest
```

### Method 2: Direct Installation

#### Prerequisites

- Python 3.6+
- pip (Python package manager)

#### Install Dependencies

```bash
pip install requests
```

#### Configure and Run

1. Copy the configuration template:
```bash
cp config.ini.example config.ini
```

2. Edit `config.ini` file (see Configuration section)

3. Run the script:
```bash
python cloudflare_ddns.py
```

## Configuration

### Multiple Domains Configuration (Recommended)

```ini
[cloudflare]
# Authentication Method 1: Using API Token (Recommended)
# Create from Cloudflare Dashboard:
# My Profile > API Tokens > Create Token
# Requires "Zone.DNS" edit permissions
api_token = your_api_token_here

# First domain configuration
[domain:ddns.example.com]
# Zone ID (Required)
zone_id = your_zone_id_here
record_type = A
ttl = 1
proxied = false

# Second domain configuration
[domain:home.example.com]
zone_id = your_zone_id_here
record_type = A
ttl = 1
proxied = true
```

### Single Domain Configuration (Legacy Support)

```ini
[cloudflare]
api_token = your_api_token_here
zone_id = your_zone_id_here
domain = your.domain.here
record_type = A
ttl = 1
proxied = false
```

### Configuration Details

- **Multiple Domain Configuration**:
  - Use `[domain:domain_name]` format for each domain section
  - Each domain can have its own zone ID, record type, and proxy settings
  - Configure any number of domains
  - All domains share the same API token

- **Configuration Parameters**:
  - `api_token`: Cloudflare API token
  - `zone_id`: Zone ID for the domain (Required)
  - `record_type`: DNS record type, typically A (IPv4) or AAAA (IPv6)
  - `ttl`: Time To Live in seconds, 1 for automatic
  - `proxied`: Enable/disable Cloudflare proxy (CDN)

### Getting Required Information

#### Getting API Token (Recommended)
1. Log in to Cloudflare Dashboard
2. Click the profile icon in the top right
3. Navigate to "My Profile" > "API Tokens"
4. Click "Create Token"
5. Use "Edit zone DNS" template or create a custom token with DNS edit permissions
6. Select applicable zones (domains)
7. Create token and copy it to the config file's api_token field

#### Getting Zone ID
1. Log in to Cloudflare Dashboard
2. Select your domain
3. Find the Zone ID in the "API" section on the right side of the overview page

## Usage

### Command Line Arguments

```bash
# Basic usage
python cloudflare_ddns.py

# Set update interval (in seconds)
python cloudflare_ddns.py -i 600  # Update every 10 minutes
python cloudflare_ddns.py --interval 3600  # Update every hour

# Specify config file path
python cloudflare_ddns.py -c /path/to/your/config.ini
```

## Setting Up as a Service

### Linux (systemd)

1. Create service file:
```bash
sudo nano /etc/systemd/system/cloudflare-ddns.service
```

2. Add the following content (modify paths):
```ini
[Unit]
Description=Cloudflare DDNS Client
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/cloudflare-ddns
ExecStart=/usr/bin/python3 /path/to/cloudflare-ddns/cloudflare_ddns.py -i 3600
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

3. Enable and start service:
```bash
sudo systemctl enable cloudflare-ddns.service
sudo systemctl start cloudflare-ddns.service
```

### macOS (launchd)

1. Create plist file:
```bash
nano ~/Library/LaunchAgents/com.user.cloudflare-ddns.plist
```

2. Add the following content (modify paths):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.cloudflare-ddns</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/cloudflare-ddns/cloudflare_ddns.py</string>
        <string>-i</string>
        <string>3600</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/path/to/cloudflare-ddns/error.log</string>
    <key>StandardOutPath</key>
    <string>/path/to/cloudflare-ddns/output.log</string>
</dict>
</plist>
```

3. Load service:
```bash
launchctl load ~/Library/LaunchAgents/com.user.cloudflare-ddns.plist
```

### Windows

Two options for running:

1. Use the provided `start_ddns.bat` script
2. Use Task Scheduler:
   - Open Task Scheduler
   - Create Basic Task
   - Set Trigger (e.g., At System Startup)
   - Choose Start a Program
   - Set program path to `python` and arguments to script path

## Logs and Cache

- Log file: `cloudflare_ddns.log`
- IP cache file: `ip_cache.json`

## License

MIT License
