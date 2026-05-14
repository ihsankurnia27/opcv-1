# Edge — Gauge Detection Device

Runs on Orange Pi (or any Linux device with camera). FastAPI + OpenCV detects analog gauge needle position, pushes readings to central server.

## Services

| Container | Port | Role |
|-----------|------|------|
| `uvls-edge` | `:8765` HTTPS | FastAPI gauge detection API + web UI |
| `uvls-edge-redirect` | `:80` HTTP | Redirects `http://` → `https://:8765` |

## Quick Start

```bash
# First time: create shared network
docker network create uvls-net

# Copy & edit config
cp config.json.example config.json
# edit config.json — set point name, calibration params, server_api_url, api_key

# Start
docker compose up -d
```

## WireGuard (remote edge)

Edge device connects to server via WireGuard tunnel. All peers need `PersistentKeepalive = 25`.

```
Orange Pi ── WG ── App Server ── Main Server
10.8.0.4        10.8.0.3        10.8.0.1 (wg-easy)
```

**Client config** (`/etc/wireguard/opiz3-edge-1.conf`):

```ini
[Interface]
Address = 10.8.0.4/32
PrivateKey = <key>

[Peer]
PublicKey = <server-key>
Endpoint = wg-01.example.com:55555
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

`PersistentKeepalive = 25` keeps NAT hole open. Without it, tunnel drops after ~2 minutes of idle traffic. Must be set on **every** peer (edge + app server).

## HTTP→HTTPS Redirect

Access `http://<edge-ip>` (port 80) auto-redirects to `https://<edge-ip>:8765`.  
The redirect container is `nginx:alpine`, no config needed beyond default.conf.

## Git Setup

```bash
# Clone on edge device
git clone https://github.com/ihsankurnia27/opcv-1.git /root/opcv-1
ln -s /root/opcv-1/edge /root/edge
cp /root/edge/config.json.example /root/edge/config.json
# edit config.json with real secrets
```

`config.json` is gitignored — secrets never committed.

**Camera**: USB camera on Orange Pi is `/dev/video1` (video0 = SoC hw encoder). Set `"camera_id": 1` in config.json. Compose mounts only `/dev/video0` by default — add entries for other devices as needed.

## Auto-Update (cron)

```bash
crontab -e

# Add: every 10 min, check for updates and rebuild
*/10 * * * * cd /root/opcv-1 && git pull >> /var/log/edge-update.log 2>&1 && cd /root/edge && docker compose up -d --build >> /var/log/edge-update.log 2>&1
```

## Gauge Detection Pipeline

1. Center detection (`find_gauge_center`): blob detector → HoughCircles fallback
2. Frame resized to **480px** internally (`_DETECT_USE_W`) for ~2× faster CV ops
3. Coords upscaled back to original resolution after detection
4. Optional Gaussian blur + adaptive threshold
5. Radial sampling — pixel intensity along 360 rays at configurable `inner_ratio`/`outer_ratio`
6. Darkest ray = needle position, parabola fit for sub-degree precision
7. `angle_to_value()` — shared linear interpolation with wrap-around → value

## Smoothing

`ValueFilter` (median window + EMA + spike rejection) runs in both:
- **Stream detect loop** — `api.py` reader thread, filter re-initialized on config changes
- **Scheduled pusher** — `push_readings.py`

Config keys: `filter_alpha` (EMA rate, default 0.15), `filter_max_jump` (spike threshold, default 1.5), `filter_window` (median window size, default 5). Web UI has smoothing controls in config panel. Spike rejection allows up to 5 consecutive jumps before accepting.

## Web UI

Light gallery theme with neon pink (#e11d48) accents. Instrument Serif + Sora fonts. Features:
- Live MJPEG feed with detection HUD overlay (value, angle, center, status)
- **Debug stream modes:** Annotated, Raw, Preprocessed (grayscale), Preprocessed + Ann, Binary (BW), Binary + Ann
- Edge Cam (device stream) and Client Cam (getUserMedia) modes
- Auto-calibrate (variance gap detection) and Manual Cal (tap-to-mark on annotated frame)
- One-shot capture, continuous detect mode
- Config save/load, camera enumeration, points list from server
- In-place update (git fetch + docker compose build)

## Detection Fine-Tuning Guide

The web UI includes 6 stream modes for debugging. Toggle them to see exactly what the algorithm sees at each stage. Detection runs at **480px** internally (`_DETECT_USE_W`), then coords are upscaled to original resolution.

### 1. Fix Flickering Binary (Lighting Instability)

Switch to **Binary (BW)** — if the white needle edges flicker/pulse, the threshold is too sensitive.

| Parameter | Try | Effect |
|-----------|-----|--------|
| `Threshold Block` | 11, 15, 21 | Higher = larger regions, ignores small lighting variations |
| `Threshold C` | 7, 9, 12 | Higher = more aggressive binarization, washes out weaker edges |

Rule: bump `threshold_block` first. Only touch `threshold_c` if edges still noisy.

### 2. Fix Needle Angle Jitter (Edge Noise)

Switch to **Binary + Ann** — if the binary image looks stable but the green needle line jumps between two positions, Hough line detection is seeing competing edges in the annulus.

| Parameter | Try | Effect |
|-----------|-----|--------|
| `Blur Kernel` | 7, 9, 11 | Smoothens grayscale before threshold, fewer spurious edges |
| `detect_method` | `radial` | Fallback to darkest-ray method — less precise but stable |

Don't exceed `Blur Kernel` 11 or the actual needle edge will blur away.

### 3. Smooth Residual Jitter

If binary and detection look mostly correct but the reported value still bounces, tighten the temporal filters.

| Parameter | Try | Effect |
|-----------|-----|--------|
| `Angle Kalman R` (measurement noise) | 0.3, 0.5 | Higher = filter trusts measurement less, smooths more |
| `Angle Kalman Q` (process noise) | 0.005, 0.001 | Lower = filter assumes needle moves slowly |
| `Filter Alpha` (EMA) | 0.10, 0.08 | Lower = more smoothing, more lag |

Start with Kalman (`R`/`Q`) before reducing EMA alpha — Kalman adapts to movement speed better.

### 4. Fix Center Jitter

If the gauge circle jumps around frame to frame (noticed in Raw or Preprocessed + Ann):

| Parameter | Try | Effect |
|-----------|-----|--------|
| `Center EMA` | 0.20, 0.15 | Lower = smoother center tracking, but more lag on fast changes |

### Quick Workflow

1. Select **Binary + Ann** in the view dropdown
2. Check if binary edges are crisp and stable
3. If flickering → increase `Threshold Block` / `Threshold C`
4. If binary stable but green needle doesn't match the real gauge needle → increase `Blur Kernel`
5. If everything looks right but value still bounces → increase `Angle Kalman R`, decrease `Angle Kalman Q`
6. Tweak one parameter at a time, watch the HUD live

## Files

```
edge/
├── Dockerfile.edge       # Python 3.12 + OpenCV
├── docker-compose.yml    # api + redirect services
├── config.json           # Per-point calibration (gitignored)
├── config.json.example   # Template with no secrets
├── requirements.txt
├── push_readings.py      # Scheduled capture + push
├── nginx/
│   └── default.conf      # HTTP→HTTPS redirect config
├── app/
│   ├── api.py            # FastAPI endpoints
│   └── static/
│       └── index.html    # Config web UI
└── gauge_reader/         # Detection library
    ├── __init__.py       # angle_to_value() helper
    ├── find_gauge_center.py
    ├── find_needle_radial.py
    ├── read_gauge.py
    └── value_filter.py   # EMA + median + spike rejection
```

## Config Reference (config.json)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `point` | string | `"G-01"` | Gauge point identifier |
| `min_value` / `max_value` | float | `0` / `10` | Gauge value range |
| `min_angle` / `max_angle` | float | `45` / `315` | Needle angle range (degrees) |
| `center_offset_y` | float | `0` | Vertical center adjustment (px) |
| `inner_ratio` | float | `0.60` | Inner sampling radius fraction |
| `outer_ratio` | float | `0.80` | Outer sampling radius fraction |
| `blur_kernel` | int | `5` | Gaussian blur kernel (0 = skip) |
| `threshold_block` | int | `0` | Adaptive threshold block (0 = skip) |
| `threshold_c` | int | `5` | Adaptive threshold constant |
| `camera_id` | int | `0` | V4L2 device ID |
| `cam_resolution` | string | `"0x0"` | Capture resolution (0x0 = native) |
| `interval_seconds` | int | `3600` | Push interval (scheduled pusher) |
| `server_api_url` | string | — | Server receive endpoint |
| `api_key` | string | — | Pre-shared API key |
| `filter_alpha` | float | `0.15` | EMA smoothing rate |
| `filter_max_jump` | float | `1.5` | Spike rejection threshold |
| `filter_window` | int | `5` | Median filter window size |
| `learned_cal` | object | — | Per-point auto-cal params (set by Learn Calibration) |
