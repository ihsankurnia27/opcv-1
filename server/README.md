# UVLS — Utility Logsheet Monitoring System

Record & view operational logsheet data across 3 shifts. Analog gauge meter reading via computer vision on **separate edge device** (Orange Pi), pushing readings to central server.

## Architecture

```
┌─ Edge (Orange Pi) ───────────────────────┐
│  Python FastAPI + OpenCV                 │
│  Web UI :8765 — config point + params    │
│  push_readings.py — periodic detect +    │
│    POST to server API                    │
│  gauge_reader/ — detection library       │
└────────────────┬─────────────────────────┘
                 │ HTTP (Tailscale / LAN)
                 ▼
┌─ Server ─────────────────────────────────┐
│  PHP Apache :8082                        │
│  MySQL :3310                             │
│  api/receive_reading.php ← edge pushes   │
│  testing.php — upload + edge readings    │
│  all PHP/JS/CSS for dashboard + recap    │
└──────────────────────────────────────────┘
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
docker compose up -d
```

Edge web UI: http://localhost:8765 — configure point, calibration, server URL.

### 4. (Dev) Push a test reading

```bash
cd edge
pip install opencv-python fastapi uvicorn  # or run inside container
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
- Manual upload → cURL to edge API → result with annotated image
- Edge Readings tab — latest pushes from Orange Pi
- Per-account config persistence via JSON files

**Gauge Meter Reader (Edge)**
- Config web UI at `http://<edge-ip>:8765/`
- Periodic scheduled captures with configurable interval
- Local test-capture to verify calibration
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
│   ├── proses_testing.php   # Upload → edge API via cURL
│   ├── proxy_detect.php     # PHP→FastAPI proxy (env URL)
│   └── ... all PHP/JS/CSS ...
│
├── edge/                    # Edge device stack (Orange Pi)
│   ├── docker-compose.yml   # api service, camera passthrough
│   ├── Dockerfile.edge      # Python 3.12 + OpenCV
│   ├── config.json          # Point + calibration + schedule
│   ├── app/
│   │   ├── api.py           # FastAPI: detect, config, test-capture
│   │   └── static/index.html  # Config web UI
│   ├── gauge_reader/        # Detection library
│   └── push_readings.py     # Scheduled pusher
│
└── uvls/                    # Cleaned up (old monolith files)
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
- Edge compose maps `:8765` (not `:80`) — `docker compose run push_readings --oneshot` for test
- Camera passthrough: uncomment `devices:` in `edge/docker-compose.yml` on Orange Pi
