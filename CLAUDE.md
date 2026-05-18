# CLAUDE.md

## Project Overview

Utility Logsheet Monitoring System — analog gauge meter reading via computer vision. Three-tier: **edge** (Orange Pi + camera) → **server** (PHP app) → **main server** (WireGuard + git origin).

## Architecture

| Layer | IP | Stack |
|-------|----|-------|
| Edge (Orange Pi) | 10.8.0.4 | FastAPI + OpenCV, nginx redirect, USB camera |
| App Server | 10.8.0.3 | PHP Apache + MySQL, receives edge readings |
| Main Server | 10.8.0.1 | wg-easy, git origin, dev environment |

## Key Files

| File | Role |
|------|------|
| `server/` | PHP/MySQL web app (port 8082) |
| `edge/` | Python FastAPI gauge detection (port 8765) |
| `server/README.md` | Full project docs |
| `edge/README.md` | Edge deployment docs |
| `README.local.md` | **Infrastructure secrets — gitignored** |
| `.gitignore` | Excludes `config.json`, `.env`, `README.local.md` |

## Dev Workflow

```
Main server: edit → commit → push
Edge device: cron git pull every 10min → auto rebuild
```

## WireGuard

- Network: `10.8.0.0/24`
- VPN server: wg-easy on 10.8.0.1 (port 55555)
- All peers: `PersistentKeepalive = 25` required

## Deployment

### 1. Server (10.8.0.3)

**IMPORTANT**: `docker compose` does NOT build frontend assets (CSS/JS/Vendor). You MUST build locally and sync.

```bash
# A. Build assets locally (requires Node + Gulp)
cd server
npm install
gulp build    # Compiles SCSS, minifies JS, copies vendor files

# B. Sync code and assets to server
# Use rsync to ensure vendor/, css/, and js/ are included (node_modules excluded)
rsync -avz --exclude='node_modules' ./server/ youri@10.8.0.3:/home/youri/opcv-1/server/

# C. Deploy on remote
ssh -i ~/key1 youri@10.8.0.3 "cd /home/youri/opcv-1/server && docker compose up -d --build"
```

### 2. Edge (10.8.0.4)

Password: `orangepi`

```bash
# Manual update
sshpass -p orangepi ssh root@10.8.0.4 "cd /root/opcv-1 && git pull && cd /root/edge && docker compose up -d --build"
```

## Database

- **DB**: `ua1-1` (root/empty on mysql:8.0, port 3310)
- **Tables**: `login` (users), `sheetsatu` (data with templates), `logsheet` (legacy)
- See `server/CLAUDE.md` for full schema

## Known Issues

- SQL injection in multiple PHP files (raw `$_POST`/`$_GET`)
- Plaintext passwords in `fbd_storage.sql`
- Exports use `\t\n` line endings (not true XLSX)
- Docker DNS on x86_64 hosts may need `daemon.json: {"dns": ["1.1.1.1", "8.8.8.8"]}`
