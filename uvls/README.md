# UVLS — Utility Logsheet Monitoring System

Record & view operational logsheet data across 3 shifts. Includes analog gauge meter reading via computer vision.

## Stack

PHP 8.3 + MySQL 8.0 — SB Admin 2 (Bootstrap 4) — Python 3.12 + OpenCV (FastAPI) — Docker Compose

## Quick Start

```bash
docker compose up -d
```

Web: http://localhost:8082 — API docs: http://localhost:8765/docs

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

**Gauge Meter Reader**
- Camera live feed + image upload → Python API needle detection
- Configurable calibration (angles, values, sampling, preprocessing)
- Per-account config persistence via JSON files

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
├── index*.php, inputdata*.php    # Logsheet CRUD
├── testing.php, api.py            # Gauge reader UI + API
├── gauge_reader/                  # Python detection lib
├── proses_testing.php             # Upload handler
├── proxy_detect.php               # PHP→FastAPI proxy
├── save/load_gauge_config.php     # Per-user config
└── koneksi.php, cek*.php          # DB + auth
```

## Notes

- Auth uses plaintext passwords (as-shipped)
- First `docker compose up` installs opencv-python (slow on arm64)
