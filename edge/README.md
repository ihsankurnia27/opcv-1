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

**Camera**: USB camera on Orange Pi is `/dev/video1` (video0 = SoC hw encoder). Set `"camera_id": 1` in config.json. Compose mounts all three video devices.

## Auto-Update (cron)

```bash
crontab -e

# Add: every 10 min, check for updates and rebuild
*/10 * * * * cd /root/opcv-1 && git pull >> /var/log/edge-update.log 2>&1 && cd /root/edge && docker compose up -d --build >> /var/log/edge-update.log 2>&1
```

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
    ├── find_gauge_center.py
    ├── find_needle_radial.py
    ├── read_gauge.py
    └── value_filter.py
```
