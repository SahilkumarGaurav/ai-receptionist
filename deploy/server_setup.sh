#!/bin/bash
# ============================================================================
# Production Server Setup Script for RapidFlow Plumbing Voice AI
# Ubuntu 22.04/24.04 LTS
# Run as root: sudo bash server_setup.sh
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ============================================================================
# Configuration
# ============================================================================
DEPLOY_USER="deploy"
APP_DIR="/opt/rapidflow"
PYTHON_VERSION="3.11"
UV_VERSION="latest"

# ============================================================================
# Pre-flight checks
# ============================================================================
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

if ! grep -qE "Ubuntu (22.04|24.04)" /etc/os-release; then
    log_warn "This script is tested on Ubuntu 22.04/24.04. Your OS: $(lsb_release -ds)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# ============================================================================
# System updates and base packages
# ============================================================================
log_info "Updating package index and upgrading system..."
apt-get update -y
apt-get upgrade -y

log_info "Installing base packages..."
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    libsqlite3-dev \
    pkg-config \
    software-properties-common \
    ufw \
    fail2ban \
    htop \
    vim \
    ca-certificates \
    gnupg \
    lsb-release

# ============================================================================
# Install Python 3.11
# ============================================================================
log_info "Installing Python ${PYTHON_VERSION}..."
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip

# Set python3.11 as default python3
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1
update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1

log_info "Python version: $(python3 --version)"

# ============================================================================
# Install uv (fast Python package manager)
# ============================================================================
log_info "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
# uv installs to ~/.local/bin, add to PATH for root
export PATH="/root/.local/bin:$PATH"
echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc

# Also make uv available system-wide
ln -sf /root/.local/bin/uv /usr/local/bin/uv
ln -sf /root/.local/bin/uvx /usr/local/bin/uvx

log_info "uv version: $(uv --version)"

# ============================================================================
# Create deploy user
# ============================================================================
log_info "Creating deploy user: ${DEPLOY_USER}..."
if id "${DEPLOY_USER}" &>/dev/null; then
    log_warn "User ${DEPLOY_USER} already exists"
else
    useradd -m -s /bin/bash -G sudo "${DEPLOY_USER}"
    # Set up passwordless sudo for deploy user (for systemctl commands)
    echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD: /bin/systemctl start rapidflow-*, /bin/systemctl stop rapidflow-*, /bin/systemctl restart rapidflow-*, /bin/systemctl status rapidflow-*, /bin/systemctl reload rapidflow-*, /bin/systemctl enable rapidflow-*, /bin/systemctl disable rapidflow-*" > /etc/sudoers.d/rapidflow-deploy
    chmod 440 /etc/sudoers.d/rapidflow-deploy
fi

# Set up SSH key for deploy user (copy from root if exists)
if [[ -d /root/.ssh ]]; then
    mkdir -p /home/${DEPLOY_USER}/.ssh
    cp /root/.ssh/authorized_keys /home/${DEPLOY_USER}/.ssh/authorized_keys 2>/dev/null || true
    chown -R ${DEPLOY_USER}:${DEPLOY_USER} /home/${DEPLOY_USER}/.ssh
    chmod 700 /home/${DEPLOY_USER}/.ssh
    chmod 600 /home/${DEPLOY_USER}/.ssh/authorized_keys 2>/dev/null || true
fi

# ============================================================================
# Install Nginx
# ============================================================================
log_info "Installing Nginx..."
apt-get install -y nginx

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# ============================================================================
# Configure UFW Firewall
# ============================================================================
log_info "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

log_info "Firewall status:"
ufw status verbose

# ============================================================================
# Configure fail2ban for SSH protection
# ============================================================================
log_info "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = %(sshd_log)s
maxretry = 3
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# ============================================================================
# Create application directory structure
# ============================================================================
log_info "Creating application directory: ${APP_DIR}..."
mkdir -p "${APP_DIR}"
mkdir -p "${APP_DIR}/logs"
mkdir -p "${APP_DIR}/public"
mkdir -p "${APP_DIR}/gcal"
mkdir -p /var/log/rapidflow

chown -R ${DEPLOY_USER}:${DEPLOY_USER} "${APP_DIR}"
chown -R ${DEPLOY_USER}:${DEPLOY_USER} /var/log/rapidflow

# ============================================================================
# Set up log rotation
# ============================================================================
log_info "Setting up logrotate..."
cat > /etc/logrotate.d/rapidflow << 'EOF'
/var/log/rapidflow/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        systemctl reload rapidflow-api rapidflow-ws > /dev/null 2>&1 || true
    endscript
}
EOF

# ============================================================================
# Generate systemd service files
# ============================================================================
log_info "Creating systemd service files..."

# API Server service
cat > /etc/systemd/system/rapidflow-api.service << 'EOF'
[Unit]
Description=RapidFlow Plumbing API Server (FastAPI)
After=network.target
Wants=network-online.target

[Service]
Type=exec
User=deploy
Group=deploy
WorkingDirectory=/opt/rapidflow
Environment=PATH=/opt/rapidflow/.venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=-/opt/rapidflow/.env
ExecStart=/opt/rapidflow/.venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info --access-log
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/rapidflow /var/log/rapidflow
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
RemoveIPC=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=append:/var/log/rapidflow/api.log
StandardError=append:/var/log/rapidflow/api-error.log
SyslogIdentifier=rapidflow-api

[Install]
WantedBy=multi-user.target
EOF

# WebSocket Server service
cat > /etc/systemd/system/rapidflow-ws.service << 'EOF'
[Unit]
Description=RapidFlow Plumbing WebSocket Server (Twilio/Deepgram)
After=network.target
Wants=network-online.target

[Service]
Type=exec
User=deploy
Group=deploy
WorkingDirectory=/opt/rapidflow
Environment=PATH=/opt/rapidflow/.venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=-/opt/rapidflow/.env
ExecStart=/opt/rapidflow/.venv/bin/python main.py
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/rapidflow /var/log/rapidflow
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
RemoveIPC=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=append:/var/log/rapidflow/ws.log
StandardError=append:/var/log/rapidflow/ws-error.log
SyslogIdentifier=rapidflow-ws

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rapidflow-api rapidflow-ws

log_info "Systemd services created and enabled"

# ============================================================================
# Create Nginx configuration
# ============================================================================
log_info "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/rapidflow << 'EOF'
# RapidFlow Plumbing - Nginx Reverse Proxy
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # SSL Configuration (certificates managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/your-domain.com/chain.pem;

    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=()" always;

    # HSTS (enable after confirming SSL works)
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root for static files and Let's Encrypt
    root /opt/rapidflow/public;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml application/rss+xml image/svg+xml;

    # WebSocket endpoint for Twilio/Deepgram streaming
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_connect_timeout 60;
        
        # Buffer settings for real-time audio
        proxy_buffering off;
        proxy_cache off;
    }

    # Alternative WebSocket path (if using different path)
    location /websocket {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_connect_timeout 60;
        proxy_buffering off;
        proxy_cache off;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Dashboard / static files
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }

    # Health check endpoint (no auth, for load balancers)
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/api/health;
        proxy_set_header Host $host;
    }

    # Logging
    access_log /var/log/nginx/rapidflow-access.log;
    error_log /var/log/nginx/rapidflow-error.log;
}
EOF

ln -sf /etc/nginx/sites-available/rapidflow /etc/nginx/sites-enabled/rapidflow

# Test nginx config
nginx -t

log_info "Nginx configuration created"

# ============================================================================
# Create deployment helper script
# ============================================================================
log_info "Creating deployment helper script..."
cat > /usr/local/bin/rapidflow-deploy << 'EOF'
#!/bin/bash
# RapidFlow deployment helper
# Usage: rapidflow-deploy [pull|build|restart|logs|status]

set -euo pipefail

APP_DIR="/opt/rapidflow"
SERVICE_API="rapidflow-api"
SERVICE_WS="rapidflow-ws"

cmd="${1:-help}"

case "$cmd" in
    pull)
        echo "Pulling latest code..."
        cd "$APP_DIR"
        sudo -u deploy git pull
        ;;
    build)
        echo "Installing dependencies with uv..."
        cd "$APP_DIR"
        sudo -u deploy uv sync --frozen
        ;;
    restart)
        echo "Restarting services..."
        systemctl restart "$SERVICE_API" "$SERVICE_WS"
        systemctl status "$SERVICE_API" "$SERVICE_WS" --no-pager
        ;;
    stop)
        echo "Stopping services..."
        systemctl stop "$SERVICE_API" "$SERVICE_WS"
        ;;
    start)
        echo "Starting services..."
        systemctl start "$SERVICE_API" "$SERVICE_WS"
        systemctl status "$SERVICE_API" "$SERVICE_WS" --no-pager
        ;;
    status)
        systemctl status "$SERVICE_API" "$SERVICE_WS" --no-pager
        ;;
    logs)
        service="${2:-}"
        case "$service" in
            api) journalctl -u "$SERVICE_API" -f ;;
            ws)  journalctl -u "$SERVICE_WS" -f ;;
            nginx) tail -f /var/log/nginx/rapidflow-access.log /var/log/nginx/rapidflow-error.log ;;
            *)   journalctl -u "$SERVICE_API" -u "$SERVICE_WS" -f ;;
        esac
        ;;
    db)
        echo "Opening SQLite database..."
        sqlite3 "$APP_DIR/calendar.db"
        ;;
    help|*)
        cat << 'HELP'
RapidFlow Deployment Helper

Usage: rapidflow-deploy <command>

Commands:
  pull      - Pull latest code from git
  build     - Install/update Python dependencies (uv sync)
  restart   - Restart both API and WebSocket services
  start     - Start both services
  stop      - Stop both services
  status    - Show service status
  logs [api|ws|nginx] - Follow logs (default: both services)
  db        - Open SQLite database shell
  help      - Show this help

Examples:
  rapidflow-deploy pull && rapidflow-deploy build && rapidflow-deploy restart
  rapidflow-deploy logs api
  rapidflow-deploy status
HELP
        ;;
esac
EOF

chmod +x /usr/local/bin/rapidflow-deploy

# ============================================================================
# Final steps
# ============================================================================
log_info "=========================================="
log_info "Server setup complete!"
log_info "=========================================="
echo
log_info "Next steps:"
echo "  1. Clone your repository to ${APP_DIR}:"
echo "     sudo -u deploy git clone <your-repo-url> ${APP_DIR}"
echo "  2. Set up secrets (see SECRETS_SETUP.md)"
echo "  3. Run: rapidflow-deploy build"
echo "  4. Configure Nginx SSL with Certbot:"
echo "     sudo certbot --nginx -d your-domain.com"
echo "  5. Start services: rapidflow-deploy start"
echo "  6. Check status: rapidflow-deploy status"
echo
log_info "Helper command: rapidflow-deploy"
log_info "Services: rapidflow-api (port 8000), rapidflow-ws (port 5000)"
log_info "Logs: /var/log/rapidflow/"