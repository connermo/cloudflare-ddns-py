# Cloudflare DDNS 客户端

一个简单的 Python 脚本，用于自动获取公网 IP 地址并更新 Cloudflare DNS 记录，实现动态 DNS（DDNS）功能。

## 功能特点

- 支持多域名配置，可同时更新多个域名的 DNS 记录
- 自动获取公网 IP 地址（使用多个 IP 查询服务以提高可靠性）
- 自动更新 Cloudflare DNS 记录
- 支持定时自动更新
- 缓存 IP 地址，避免不必要的 API 调用
- 详细的日志记录
- 支持 Docker 部署

## 安装和运行

### 方式一：使用 Docker（推荐）

1. 复制配置文件模板：
```bash
cp config.ini.example config.ini
```

2. 编辑 `config.ini` 文件

3. 启动容器（选择一种方式）：

#### 使用 docker-compose（推荐）
```bash
docker-compose up -d
```

#### 使用 Docker 命令
```bash
docker run -d \
  --name cloudflare-ddns \
  -v $(pwd)/config.ini:/config/config.ini:ro \
  -e UPDATE_INTERVAL=300 \
  --restart unless-stopped \
  connermo/cloudflare-ddns-py:latest
```

### 方式二：直接运行

#### 前提条件

- Python 3.6+
- pip（Python 包管理器）

#### 安装依赖

```bash
pip install requests
```

#### 配置和运行

1. 复制配置文件模板：
```bash
cp config.ini.example config.ini
```

2. 编辑 `config.ini` 文件（详见配置说明部分）

3. 运行脚本：
```bash
python cloudflare_ddns.py
```

## 配置说明

### 多域名配置（推荐）

```ini
[cloudflare]
# Cloudflare API 令牌
api_token = your_api_token_here

# 第一个域名配置
[domain:ddns.example.com]
# zone_id 是必填项
zone_id = your_zone_id_here
record_type = A
ttl = 1
proxied = false

# 第二个域名配置
[domain:home.example.com]
zone_id = your_zone_id_here
record_type = A
ttl = 1
proxied = true
```

### 单域名配置（向后兼容）

```ini
[cloudflare]
api_token = your_api_token_here
zone_id = your_zone_id_here
domain = your.domain.here
record_type = A
ttl = 1
proxied = false
```

### 配置项说明

- **多域名配置**：
  - 使用 `[domain:域名]` 格式为每个域名创建独立的配置部分
  - 每个域名配置都可以有自己的区域 ID、记录类型和代理设置
  - 可以配置任意数量的域名
  - 所有域名共用同一个 API 令牌

- **配置项说明**：
  - `api_token`：Cloudflare API 令牌
  - `zone_id`：域名所在的区域 ID（必填）
  - `record_type`：DNS 记录类型，通常为 A（IPv4）或 AAAA（IPv6）
  - `ttl`：生存时间（秒），1 表示自动
  - `proxied`：是否启用 Cloudflare 代理（CDN）

### 获取必要信息

#### 获取 API 令牌（推荐）
1. 登录 Cloudflare 控制面板
2. 点击右上角的个人资料图标
3. 选择"我的个人资料" > "API 令牌"
4. 点击"创建令牌"
5. 使用"编辑区域 DNS"模板，或创建自定义令牌（确保有 DNS 编辑权限）
6. 选择适用的区域（域名）
7. 创建令牌并复制到配置文件的 api_token 字段

#### 获取区域 ID
1. 登录 Cloudflare 控制面板
2. 选择您的域名
3. 在概述页面右侧的"API"部分可以找到区域 ID

## 使用方法

### 命令行参数

```bash
# 基本用法
python cloudflare_ddns.py

# 设置更新间隔（单位：秒）
python cloudflare_ddns.py -i 600  # 每 10 分钟更新
python cloudflare_ddns.py --interval 3600  # 每小时更新

# 指定配置文件路径
python cloudflare_ddns.py -c /path/to/your/config.ini
```

### 环境变量（Docker）

- `CONFIG_PATH`：配置文件路径，默认为 `/config/config.ini`
- `UPDATE_INTERVAL`：更新间隔（秒），默认为 300 秒

## 设置为系统服务

### Linux (systemd)

1. 创建服务文件：
```bash
sudo nano /etc/systemd/system/cloudflare-ddns.service
```

2. 添加以下内容（请修改路径）：
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

3. 启用并启动服务：
```bash
sudo systemctl enable cloudflare-ddns.service
sudo systemctl start cloudflare-ddns.service
```

### macOS (launchd)

1. 创建 plist 文件：
```bash
nano ~/Library/LaunchAgents/com.user.cloudflare-ddns.plist
```

2. 添加以下内容（请修改路径）：
```