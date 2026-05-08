# UVLS — Utility Logsheet Monitoring System

Record & view operational logsheet data across 3 shifts. Analog gauge meter reading via computer vision on **separate edge device** (Orange Pi), pushing readings to central server.

## Architecture

```
┌─ Edge (Orange Pi) ───────────────────────────┐
│  :80 nginx (http→https redirect)             │
│  :8765 FastAPI + OpenCV (HTTPS)              │
│  USB camera on /dev/video1 (640x480)         │
│  push_readings.py — periodic detect + POST   │
│  Auto-update: cron git pull every 10min      │
└────────────────┬─────────────────────────────┘
                 │ WireGuard 10.8.0.0/24
                 │ PersistentKeepalive = 25
                 ▼
┌─ App Server (10.8.0.3) ──────────────────────┐
│  uvls-app :8082 (PHP Apache)                 │
│  uvls-mysql :3310                            │
│  WireGuard keepalive = 25                    │
└────────────────┬─────────────────────────────┘
                 │ LAN
                 ▼
┌─ Main Server (10.8.0.1) ─────────────────────┐
│  wg-easy — WireGuard server                  │
│  Git origin — development + push             │
└──────────────────────────────────────────────┘
```

**Edge → Server only.** Edge is active: captures, detects, pushes. Server passively receives.

## Quick Start

### 1. Create shared network

```bash
docker network create uvls-net
```

### 2. Start server (monitoring + DB)

```bash
cd server
docker compose up -d
```

Web: http://localhost:8082

### 3. Start edge (detection)

```bash
cd edge
cp config.json.example config.json   # edit secrets (point, angles, server_api_url, api_key)
docker compose up -d
```

Edge web UI: http://edge-ip (auto-redirects to https://edge-ip:8765)

**Camera**: USB camera is usually `/dev/video1` (not video0). Edit `config.json` → `"camera_id": 1`. Compose mounts `video0/1/2` by default.

### 4. (Dev) Push a test reading

```bash
cd edge
pip install opencv-python fastapi uvicorn
python push_readings.py --oneshot
```

### Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin | Admin |
| ut1 | ut1 | UT1 |
| ut2 | ut2 | UT2 |
| guest | guest | Guest |

## Features

**Logsheet Management**
- 3-shift data entry, per-role dashboards, date filtering, Excel export, Chart.js graphs

**Gauge Meter Reader (Server)**
- Manual upload → proxy to edge API → result with annotated image
- Edge Readings tab — latest pushes from Orange Pi
- Per-account config persistence via JSON files

**Gauge Meter Reader (Edge)**
- Config web UI at `http://<edge-ip>`
- Periodic scheduled captures with configurable interval
- Local test-capture to verify calibration
- HTTP→HTTPS auto-redirect via nginx
- POSTs readings (value, angle, base64 annotated image) to server

## Gauge Detection Pipeline

1. Center detection (blob detector / HoughCircles)
2. Optional Gaussian blur + adaptive threshold
3. Radial sampling — pixel intensity along 360 rays
4. Darkest ray = needle position
5. Parabola fit for sub-degree precision
6. Linear interpolation with wrap-around → value

## Shift Schedule

| Shift | Hours |
|-------|-------|
| 1 | 06:00 – 13:59 |
| 2 | 14:00 – 21:59 |
| 3 | 22:00 – 05:59 |

## Database

- `login` — users (Admin, UT1, UT2, Guest)
- `sheetsatu` — main data (template rows with NULL tanggal, cloned per date)

## Project Layout

```
├── server/                  # Central stack
│   ├── docker-compose.yml   # db + app
│   ├── Dockerfile           # PHP Apache + curl + mysqli
│   ├── api/receive_reading.php  # Edge push endpoint
│   ├── testing.php          # Upload + edge readings tab
│   ├── proses_testing.php   # Upload → edge API via proxy
│   ├── proxy_detect.php     # PHP→FastAPI proxy (env URL)
│   └── ... all PHP/JS/CSS ...
│
├── edge/                    # Edge device stack (Orange Pi)
│   ├── docker-compose.yml   # api + redirect services
│   ├── Dockerfile.edge      # Python 3.12 + OpenCV
│   ├── config.json          # Per-point calibration (gitignored)
│   ├── config.json.example  # Template with no secrets
│   ├── push_readings.py     # Scheduled pusher
│   ├── nginx/default.conf   # HTTP→HTTPS redirect
│   ├── app/api.py           # FastAPI endpoints
│   └── gauge_reader/        # Detection library
│
├── .gitignore
├── edge/README.md           # Edge deployment docs
└── server/README.md         # This file
```

## Git Workflow

```bash
# Main server — edit code, commit, push
cd /home/ihsan/opcv-1
git add -A
git commit -m "what changed"
git push

# Edge device — auto-pulls every 10 min via cron
# Or manual:
ssh root@10.8.0.4 "cd /root/opcv-1 && git pull && cd /root/edge && docker compose up -d --build"
```

## Environment Variables

### Server compose

| Variable | Default | Description |
|----------|---------|-------------|
| `GAUGE_API_URL` | `http://edge:8765/detect` | Edge device detection endpoint |

### Edge compose

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_API_URL` | `http://uvls-app/api/receive_reading.php` | Server receive endpoint |
| `EDGE_API_KEY` | `changeme` | Shared API key for auth |

## Notes

- Auth uses plaintext passwords (as-shipped)
- Edge web UI accessible on port 80 (auto-redirects to 8765 HTTPS)
- Camera passthrough mounts `/dev/video0`, `/dev/video1`, `/dev/video2` — USB camera on Orange Pi is device 1
- `gitignore` excludes `config.json` (secrets) — always use `config.json.example` as template
- WireGuard clients need `PersistentKeepalive = 25` to prevent NAT drop (set on both edge 10.8.0.4 and app server 10.8.0.3)
- App server (10.8.0.3) needed Docker daemon DNS fix: `daemon.json: {"dns": ["1.1.1.1", "8.8.8.8"]}`
