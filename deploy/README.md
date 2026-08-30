# RapidFlow Plumbing - Production Deployment

Complete deployment assets for running the RapidFlow Plumbing Voice AI on Ubuntu 22.04/24.04 VPS.

## Quick Start

```bash
# 1. Run server setup (as root)
sudo bash server_setup.sh

# 2. Clone repository (as deploy user)
sudo -u deploy -i
cd /opt/rapidflow
git clone <your-repo-url> .

# 3. Configure secrets
# Follow SECRETS_SETUP.md to create .env, credentials.json, token.json

# 4. Build and start
rapidflow-deploy build
rapidflow-deploy start

# 5. Configure SSL with Certbot
sudo certbot --nginx -d your-domain.com

# 6. Update Nginx config with your domain, then reload
sudo nginx -t && sudo systemctl reload nginx
```

## Files in This Directory

| File | Description |
|------|-------------|
| `server_setup.sh` | Complete server provisioning script (run as root) |
| `rapidflow-api.service` | Systemd service for FastAPI (port 8000) |
| `rapidflow-ws.service` | Systemd service for WebSocket server (port 5000) |
| `nginx.conf` | Nginx reverse proxy with WebSocket support |
| `rapidflow-deploy` | Deployment helper CLI (installed to /usr/local/bin) |
| `SECRETS_SETUP.md` | Step-by-step secrets configuration guide |

## Architecture

```
Internet (HTTPS)
    │
    ▼
┌─────────────────────────────────────┐
│         Nginx (443/80)              │
│  - SSL termination                  │
│  - Static file serving (public/)    │
│  - Rate limiting, security headers  │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
  /api/*           /ws, /websocket
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ FastAPI     │  │ WebSocket   │
│ (port 8000) │  │ (port 5000) │
│ 2 workers   │  │ single proc │
└─────────────┘  └─────────────┘
       │               │
       └───────┬───────┘
               ▼
       ┌─────────────┐
       │  SQLite     │
       │ calendar.db │
       └─────────────┘
```

## Service Management

```bash
# Using helper (recommended)
rapidflow-deploy status
rapidflow-deploy restart
rapidflow-deploy logs api
rapidflow-deploy logs ws

# Or directly with systemctl
sudo systemctl status rapidflow-api rapidflow-ws
sudo systemctl restart rapidflow-api rapidflow-ws
sudo journalctl -u rapidflow-api -f
```

## Ports

| Service | Port | Access |
|---------|------|--------|
| Nginx HTTP | 80 | Public (redirects to HTTPS) |
| Nginx HTTPS | 443 | Public (main entry) |
| FastAPI | 8000 | Localhost only (proxied) |
| WebSocket | 5000 | Localhost only (proxied) |
| SSH | 22 | Public (key-only) |

## Security Features

- **Non-root user**: `deploy` user with minimal sudo
- **Systemd hardening**: NoNewPrivileges, ProtectSystem=strict, etc.
- **UFW firewall**: Only 22, 80, 443 open
- **fail2ban**: SSH brute-force protection
- **File permissions**: Secrets at 600, DB at 640
- **Nginx security headers**: CSP, HSTS, X-Frame-Options, etc.
- **Log rotation**: 30 days retention, compressed

## SSL/TLS

Certbot manages Let's Encrypt certificates automatically:

```bash
# Initial setup
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (installed by certbot)
sudo systemctl status certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

## Monitoring

```bash
# Service health
rapidflow-deploy test

# Resource usage
htop
df -h /opt/rapidflow

# Logs
rapidflow-deploy logs
tail -f /var/log/rapidflow/api.log
tail -f /var/log/rapidflow/ws.log
tail -f /var/log/nginx/rapidflow-access.log
```

## Updates

```bash
# Pull and deploy new version
rapidflow-deploy pull
rapidflow-deploy build
rapidflow-deploy restart

# Or manually:
cd /opt/rapidflow
sudo -u deploy git pull
sudo -u deploy uv sync --frozen
sudo systemctl restart rapidflow-api rapidflow-ws
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Service won't start | `journalctl -u rapidflow-api -n 50` |
| WebSocket connection fails | Check Nginx `/ws` config, verify port 5000 |
| Google Calendar auth fails | Delete `token.json`, restart service |
| Database locked | Ensure only one process writes; check for stale locks |
| SSL cert errors | `certbot renew`, check Nginx ssl paths |

## Backup

```bash
# Database backup
sqlite3 /opt/rapidflow/calendar.db ".backup /opt/rapidflow/backups/calendar-$(date +%F).db"

# Secrets backup (encrypted)
tar -czf - /opt/rapidflow/.env /opt/rapidflow/credentials.json /opt/rapidflow/token.json | gpg --symmetric > secrets-$(date +%F).tar.gz.gpg
```

## Support

- Check logs first: `rapidflow-deploy logs`
- Verify config: `rapidflow-deploy test`
- Review this guide: `SECRETS_SETUP.md`