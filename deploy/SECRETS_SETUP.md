# Secrets & Environment Setup Guide

This guide explains how to securely configure all required secrets on your VPS **after** cloning the repository. **Never commit these files to Git.**

---

## 1. Required Secret Files

| File | Purpose | Source |
|------|---------|--------|
| `.env` | Application environment variables | Create manually |
| `credentials.json` | Google OAuth 2.0 Client Credentials | Google Cloud Console |
| `token.json` | Google OAuth 2.0 User Token (auto-generated) | First run |

---

## 2. Create `.env` File

```bash
# Switch to deploy user
sudo -u deploy -i

# Navigate to app directory
cd /opt/rapidflow

# Create .env file with restricted permissions
cat > .env << 'EOF'
# ============================================================================
# RapidFlow Plumbing - Production Environment
# ============================================================================

# --- Deepgram (STT + TTS) ---
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# --- OpenAI (LLM Reasoning) ---
OPENAI_API_KEY=your_openai_api_key_here

# --- Google Calendar ---
GOOGLE_CALENDAR_ID=primary
TIMEZONE=America/New_York

# --- Resend (Email Confirmations) ---
RESEND_API_KEY=your_resend_api_key_here
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=RapidFlow Plumbing

# --- Twilio (Telephony) ---
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# --- WebSocket Server ---
WS_PORT=5000

# --- Optional: Sentry for error tracking ---
# SENTRY_DSN=https://xxx@sentry.io/xxx

# --- Optional: Log level ---
LOG_LEVEL=INFO
EOF

# Secure the file
chmod 600 .env
```

**Verify:** `cat .env` (ensure no trailing spaces, all keys present)

---

## 3. Google Cloud OAuth Setup (`credentials.json`)

### Step 1: Create OAuth Credentials in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create new)
3. **Enable APIs:** Google Calendar API
4. Navigate to **APIs & Services → Credentials**
5. Click **+ Create Credentials → OAuth Client ID**
6. Application type: **Desktop app**
7. Name: `RapidFlow Production`
8. Click **Create**
9. Download the JSON file

### Step 2: Upload to VPS

**Option A: SCP from local machine**
```bash
scp credentials.json deploy@your-vps-ip:/opt/rapidflow/credentials.json
```

**Option B: Create directly on VPS (paste content)**
```bash
sudo -u deploy -i
cd /opt/rapidflow
cat > credentials.json << 'EOF'
PASTE_THE_ENTIRE_JSON_CONTENT_HERE
EOF
chmod 600 credentials.json
```

### Step 3: Verify
```bash
cat /opt/rapidflow/credentials.json | jq .  # Should show valid JSON with client_id, client_secret, etc.
```

---

## 4. Generate `token.json` (First Run)

The token is generated automatically on first run via browser OAuth flow.

### On VPS (with display/forwarding):
```bash
sudo -u deploy -i
cd /opt/rapidflow
source .venv/bin/activate
python -c "
from gcal.auth import get_credentials
creds = get_credentials()
print('Token saved to token.json')
"
```
- A browser window will open (or you'll get a URL)
- Authorize the app
- `token.json` will be created in `/opt/rapidflow/`

### Headless VPS (no browser):
```bash
# Run locally on your machine first:
cd /path/to/local/repo
source .venv/bin/activate
python -c "
from gcal.auth import get_credentials
creds = get_credentials()
print('Token saved to token.json')
"
# Copy the generated token.json to VPS:
scp token.json deploy@your-vps-ip:/opt/rapidflow/token.json
```

### Secure token.json:
```bash
sudo -u deploy chmod 600 /opt/rapidflow/token.json
```

---

## 5. Verify All Secrets

```bash
sudo -u deploy -i
cd /opt/rapidflow

# Check file permissions (should be 600)
ls -la .env credentials.json token.json

# Test environment loading
source .venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['DEEPGRAM_API_KEY', 'OPENAI_API_KEY', 'RESEND_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TIMEZONE']
for k in required:
    v = os.getenv(k)
    print(f'{k}: {\"SET\" if v else \"MISSING\"}')"
```

Expected output: all `SET`

---

## 6. File Permissions Summary

| File | Owner | Permissions | Command |
|------|-------|-------------|---------|
| `.env` | deploy:deploy | 600 | `chmod 600 .env` |
| `credentials.json` | deploy:deploy | 600 | `chmod 600 credentials.json` |
| `token.json` | deploy:deploy | 600 | `chmod 600 token.json` |
| `calendar.db` | deploy:deploy | 640 | `chmod 640 calendar.db` |

---

## 7. Rotating Secrets

### Deepgram / OpenAI / Resend / Twilio:
1. Generate new key in provider dashboard
2. Update `.env` on VPS
3. Restart services: `rapidflow-deploy restart`

### Google OAuth:
1. Regenerate client secret in Google Cloud Console
2. Replace `credentials.json`
3. Delete `token.json` (will regenerate on next run)
4. Restart services

---

## 8. Backup Strategy

```bash
# Backup secrets (encrypted)
tar -czf - /opt/rapidflow/.env /opt/rapidflow/credentials.json /opt/rapidflow/token.json | gpg --symmetric --output secrets-backup-$(date +%F).tar.gz.gpg

# Restore
gpg --decrypt secrets-backup-2026-08-30.tar.gz.gpg | tar -xz -C /
```

Store backups in a secure, off-site location (password manager, encrypted drive, etc.).

---

## 9. Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json` not found | Verify path: `/opt/rapidflow/credentials.json` |
| `token.json` invalid/expired | Delete it, restart service to regenerate |
| `DEEPGRAM_API_KEY` not working | Check key has "Agent" and "STT/TTS" permissions |
| `GOOGLE_CALENDAR_ID` wrong | Use `primary` or specific calendar email |
| Timezone errors | Verify `TIMEZONE` is valid IANA zone (e.g., `America/New_York`) |

---

## Security Checklist

- [ ] `.env` permissions are `600`
- [ ] `credentials.json` permissions are `600`
- [ ] `token.json` permissions are `600`
- [ ] No secrets in Git history (check with `git log --all --full-history -- .env`)
- [ ] UFW firewall allows only 22, 80, 443
- [ ] fail2ban is running
- [ ] SSH key-only authentication (disable password auth)
- [ ] Regular security updates: `apt list --upgradable`