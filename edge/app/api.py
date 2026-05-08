import base64
import glob
import io
import json
import os
import re
import sys
import threading
import urllib.error
import urllib.request

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle, detect_scale_range, compute_variance_profile, learn_gap_params

CONFIG_PATH = os.environ.get("CONFIG_PATH", "/app/config.json")

app = FastAPI(title="Edge Gauge Reader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Config helpers ---

def load_config():
    defaults = {
        "point": "G-01",
        "min_value": 0,
        "max_value": 10,
        "min_angle": 45,
        "max_angle": 315,
        "center_offset_y": 0,
        "inner_ratio": 0.60,
        "outer_ratio": 0.80,
        "blur_kernel": 5,
        "threshold_block": 0,
        "threshold_c": 5,
        "interval_seconds": 3600,
        "server_api_url": "http://uvls-app/api/receive_reading.php",
        "api_key": "changeme",
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            defaults.update(json.load(f))
    # ensure camera defaults
    defaults.setdefault("camera_id", 0)
    defaults.setdefault("cam_resolution", "0x0")
    return defaults


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# --- Camera helpers ---

# Global lock for camera access to avoid conflicts
_camera_lock = threading.Lock()
_camera_streams = {}  # camera_id -> cv2.VideoCapture

def _probe_native_resolution(camera_id):
    """Open camera, set ultra-high res, read clamped max from driver."""
    try:
        cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            return 640, 480
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return w, h
    except Exception:
        return 640, 480


def _enumerate_cameras(max_check=8):
    """List available video device paths and open-able indices."""
    devices = []
    # check /dev/video* style
    for path in sorted(glob.glob("/dev/video*")):
        m = re.search(r'/dev/video(\d+)', path)
        if not m:
            continue
        idx = int(m.group(1))
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            mw, mh = _probe_native_resolution(idx)
            label = f"Video {idx}"
            devices.append({"id": idx, "path": path, "label": label,
                            "width": w, "height": h,
                            "max_width": mw, "max_height": mh})
    # also probe plain indices 0..max_check not found above
    found_ids = {d["id"] for d in devices}
    for idx in range(max_check):
        if idx in found_ids:
            continue
        path = f"/dev/video{idx}"
        # skip if device node doesn't exist (avoids hanging)
        if not os.path.exists(path):
            continue
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            mw, mh = _probe_native_resolution(idx)
            devices.append({"id": idx, "path": path, "label": f"Video {idx}",
                            "width": w, "height": h,
                            "max_width": mw, "max_height": mh})
    return devices


@app.get("/api/cameras")
def list_cameras():
    """Enumerate available video devices."""
    devices = _enumerate_cameras()
    if not devices:
        # fallback: include the configured default
        cfg = load_config()
        cam_id = int(cfg.get("camera_id", 0))
        mw, mh = _probe_native_resolution(cam_id)
        devices.append({"id": cam_id, "path": f"/dev/video{cam_id}",
                        "label": f"Video {cam_id}",
                        "width": 0, "height": 0,
                        "max_width": mw, "max_height": mh})
    return devices


def _get_capture(camera_id):
    cv2.destroyAllWindows()
    cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def _read_frame(cap):
    """Read a frame, return None on failure."""
    for _ in range(3):  # retry a few times
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            return frame
    return None


def _generate_mjpeg(camera_id, width=None, height=None):
    """Generator that yields MJPEG frames from camera_id."""
    cap = _get_capture(camera_id)
    if width and height:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
    try:
        while True:
            frame = _read_frame(cap)
            if frame is None:
                continue
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
    except GeneratorExit:
        pass
    finally:
        cap.release()


@app.get("/api/stream")
def stream_video(camera_id: int = Query(0), w: int = Query(0), h: int = Query(0)):
    """MJPEG stream from a camera. w=0/h=0 → auto-detect native resolution."""
    if w <= 0 or h <= 0:
        w, h = _probe_native_resolution(camera_id)
    return StreamingResponse(
        _generate_mjpeg(camera_id, w, h),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/detect-frame")
def detect_frame(camera_id: int = Form(0)):
    """Capture a single frame from camera, run detection, return annotated b64."""
    cap = _get_capture(camera_id)
    try:
        frame = _read_frame(cap)
        if frame is None:
            raise HTTPException(500, "failed to capture frame")
    finally:
        cap.release()

    cfg = load_config()
    center = find_gauge_center(frame)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    cy += int(cfg["center_offset_y"])
    angle_deg = find_needle_angle(
        frame, cx, cy, radius,
        inner_ratio=cfg["inner_ratio"],
        outer_ratio=cfg["outer_ratio"],
        blur_kernel=cfg["blur_kernel"],
        threshold_block=cfg["threshold_block"],
        threshold_c=cfg["threshold_c"],
    )

    min_a, max_a = cfg["min_angle"], cfg["max_angle"]
    min_v, max_v = cfg["min_value"], cfg["max_value"]
    new_range = max_v - min_v
    if min_a <= max_a:
        old_range = max_a - min_a
        value = ((angle_deg - min_a) * new_range) / old_range + min_v if old_range != 0 else min_v
    else:
        full_range = (360 - min_a) + max_a
        if full_range == 0:
            value = min_v
        else:
            if angle_deg >= min_a:
                needle_pos = angle_deg - min_a
            else:
                needle_pos = (360 - min_a) + angle_deg
            value = (needle_pos * new_range) / full_range + min_v
    value = max(min_v, min(max_v, value))

    cfg_dict = cfg
    annotated = draw_needle(frame.copy(), cx, cy, radius, angle_deg,
                            inner_ratio=float(cfg_dict["inner_ratio"]),
                            outer_ratio=float(cfg_dict["outer_ratio"]),
                            min_angle=min_a, max_angle=max_a)
    _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    h, w = frame.shape[:2]
    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx, "y": cy, "radius": radius},
        "annotated_image": annotated_b64,
        "error": None,
        "w": w, "h": h,
    }


# --- Auto-calibrate ---

@app.post("/api/auto-calibrate")
async def auto_calibrate(camera_id: int = Form(0), image: UploadFile = File(None)):
    """Detect scale tick-mark gap. Uses camera_id for edge cam, or uploaded image
    for client cam. Returns estimated min/max angles."""
    cfg = load_config()
    if image:
        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(500, "failed to decode uploaded image")
    else:
        try:
            cap = _get_capture(camera_id)
            frame = _read_frame(cap)
            cap.release()
            if frame is None:
                raise HTTPException(500, "failed to capture frame")
        except Exception as e:
            raise HTTPException(500, f"camera error: {e}")

    center = find_gauge_center(frame)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    point_name = cfg.get("point", "")

    # Check for learned params for this point
    learned = cfg.get("learned_cal", {}).get(point_name, {})
    vr = learned.get("variance_ratio", 0.25)
    mg = learned.get("min_gap_deg", 20)

    result = detect_scale_range(
        frame, cx, cy, radius,
        blur_kernel=3,
        threshold_block=0,
        threshold_c=0,
        variance_ratio=vr,
        min_gap_deg=mg,
    )
    if result is None:
        return {
            "error": "could not detect scale range",
            "min_angle": cfg["min_angle"],
            "max_angle": cfg["max_angle"],
        }

    min_a, max_a = result
    return {"min_angle": float(min_a), "max_angle": float(max_a), "error": None}


@app.post("/api/learn-calibration")
async def learn_calibration(
    image: UploadFile = File(...),
    center_x: float = Form(...),
    center_y: float = Form(...),
    radius: float = Form(...),
    min_angle: float = Form(...),
    max_angle: float = Form(...),
    point: str = Form(""),
):
    """Learn optimal detection params from user-indicated min/max angles.

    Takes the same image and center used during Manual Cal, extracts the
    radial variance profile, computes optimal variance_ratio for future
    auto-calibration of this gauge point. Stores per-point params in config.
    """
    cfg = load_config()
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(500, "failed to decode image")

    variances, smoothed = compute_variance_profile(
        frame, int(center_x), int(center_y), int(radius),
        blur_kernel=3, threshold_block=0, threshold_c=0,
    )
    if smoothed is None:
        return {"error": "could not compute variance profile", "learned": False}

    params = learn_gap_params(smoothed, min_angle, max_angle)
    params["min_gap_deg"] = int(abs(max_angle - min_angle) % 360)
    params["min_angle"] = float(min_angle)
    params["max_angle"] = float(max_angle)

    if point:
        learned = cfg.setdefault("learned_cal", {})
        learned[point] = params
        save_config(cfg)

    return {"learned": True, "point": point, "params": params}


# --- Config API ---

@app.get("/api/config")
def get_config():
    return load_config()


@app.post("/api/config")
def update_config(body: dict):
    cfg = load_config()
    allowed = {
        "point", "camera_id", "cam_resolution",
        "min_value", "max_value", "min_angle", "max_angle",
        "center_offset_y", "inner_ratio", "outer_ratio",
        "blur_kernel", "threshold_block", "threshold_c",
        "interval_seconds", "server_api_url", "api_key",
    }
    for k, v in body.items():
        if k in allowed:
            cfg[k] = v
    save_config(cfg)
    return {"status": "ok", "config": cfg}


@app.get("/api/points")
def proxy_points():
    """Proxy: fetch points list from server API."""
    cfg = load_config()
    server_url = cfg.get("server_api_url", "")
    if not server_url:
        raise HTTPException(502, "server_api_url not configured")
    points_url = server_url.replace("/receive_reading.php", "/get_points.php")
    try:
        req = urllib.request.Request(points_url)
        api_key = cfg.get("api_key", "")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data
    except urllib.error.URLError as e:
        raise HTTPException(502, f"server unreachable: {e.reason}")
    except json.JSONDecodeError:
        raise HTTPException(502, "invalid response from server")
    except Exception as e:
        raise HTTPException(502, str(e))


# --- Test capture ---

@app.post("/api/test-capture")
def test_capture():
    """Capture one frame from camera, detect, return result + annotated b64."""
    cfg = load_config()
    cam_id = int(cfg.get("camera_id", 0))
    try:
        cap = _get_capture(cam_id)
        frame = _read_frame(cap)
        cap.release()
        if frame is None:
            raise HTTPException(500, "failed to capture frame")
    except Exception as e:
        raise HTTPException(500, f"camera error: {e}")


    center = find_gauge_center(frame)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    cy += int(cfg["center_offset_y"])
    angle_deg = find_needle_angle(
        frame, cx, cy, radius,
        inner_ratio=cfg["inner_ratio"],
        outer_ratio=cfg["outer_ratio"],
        blur_kernel=cfg["blur_kernel"],
        threshold_block=cfg["threshold_block"],
        threshold_c=cfg["threshold_c"],
    )

    # map angle -> value
    min_a, max_a = cfg["min_angle"], cfg["max_angle"]
    min_v, max_v = cfg["min_value"], cfg["max_value"]
    new_range = max_v - min_v
    if min_a <= max_a:
        old_range = max_a - min_a
        value = ((angle_deg - min_a) * new_range) / old_range + min_v if old_range != 0 else min_v
    else:
        full_range = (360 - min_a) + max_a
        if full_range == 0:
            value = min_v
        else:
            if angle_deg >= min_a:
                needle_pos = angle_deg - min_a
            else:
                needle_pos = (360 - min_a) + angle_deg
            value = (needle_pos * new_range) / full_range + min_v
    value = max(min_v, min(max_v, value))

    annotated = draw_needle(frame.copy(), cx, cy, radius, angle_deg,
                            inner_ratio=float(cfg["inner_ratio"]),
                            outer_ratio=float(cfg["outer_ratio"]),
                            min_angle=min_a, max_angle=max_a)
    _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    h, w = frame.shape[:2]
    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx, "y": cy, "radius": radius},
        "annotated_image": annotated_b64,
        "error": None,
        "w": w, "h": h,
    }


# --- Detect endpoint (same, for external callers) ---

@app.post("/detect")
async def detect(
    image: UploadFile = File(...),
    min_angle: float = Form(45.0),
    max_angle: float = Form(315.0),
    min_value: float = Form(0.0),
    max_value: float = Form(10.0),
    center_offset_y: float = Form(0.0),
    inner_ratio: float = Form(0.60),
    outer_ratio: float = Form(0.80),
    blur_kernel: int = Form(5),
    threshold_block: int = Form(0),
    threshold_c: int = Form(5),
    need_annotation: bool = Form(True),
):
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "could not decode image"}

    center = find_gauge_center(img)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    cy_offset = cy + int(center_offset_y)
    angle_deg = find_needle_angle(img, cx, cy_offset, radius,
                                   inner_ratio=inner_ratio,
                                   outer_ratio=outer_ratio,
                                   blur_kernel=blur_kernel,
                                   threshold_block=threshold_block,
                                   threshold_c=threshold_c)

    old_range = max_angle - min_angle
    new_range = max_value - min_value
    if min_angle <= max_angle:
        if old_range == 0:
            value = min_value
        else:
            value = ((angle_deg - min_angle) * new_range) / old_range + min_value
    else:
        full_range = (360 - min_angle) + max_angle
        if full_range == 0:
            value = min_value
        else:
            if angle_deg >= min_angle:
                needle_pos = angle_deg - min_angle
            else:
                needle_pos = (360 - min_angle) + angle_deg
            value = (needle_pos * new_range) / full_range + min_value
    value = max(min_value, min(max_value, value))

    annotated_b64 = None
    if need_annotation:
        annotated = draw_needle(img.copy(), cx, cy_offset, radius, angle_deg,
                                inner_ratio=inner_ratio, outer_ratio=outer_ratio,
                                min_angle=min_angle, max_angle=max_angle)
        _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    h, w = img.shape[:2]
    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx, "y": cy_offset, "radius": radius},
        "annotated_image": annotated_b64,
        "error": None,
        "w": w, "h": h,
    }


VERSION_PATH = "/app/version.txt"
REPO_PATH = "/repo"
COMPOSE_FILE = "/repo/edge/docker-compose.yml"


@app.get("/api/version")
def get_version():
    """Return current version string from version.txt."""
    version = "unknown"
    if os.path.exists(VERSION_PATH):
        with open(VERSION_PATH) as f:
            version = f.read().strip()
    return {"version": version, "update_available": False}


@app.post("/api/update")
async def run_update():
    """Git pull + docker compose rebuild. Designed for Docker-socket access.

    Requires:
      - /var/run/docker.sock mounted into container
      - /root/opcv-1 mounted at /repo

    Returns build log. Container will restart after compose up -d.
    """
    import subprocess as sp
    logs = []
    def run(cmd, cwd=None):
        try:
            r = sp.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
            out = (r.stdout + r.stderr).strip()
            logs.append(f"$ {' '.join(cmd)}\n{out}")
            return r.returncode == 0
        except sp.TimeoutExpired:
            logs.append(f"$ {' '.join(cmd)}\n[TIMEOUT]")
            return False
        except Exception as e:
            logs.append(f"$ {' '.join(cmd)}\n[ERROR] {e}")
            return False

    if not os.path.exists(REPO_PATH):
        return {"status": "error", "log": "REPO_PATH /repo not mounted", "logs": logs}
    if not os.path.exists("/var/run/docker.sock"):
        return {"status": "error", "log": "Docker socket not mounted", "logs": logs}

    # Step 1: git fetch + reset — safe even on dirty tree
    run(["git", "fetch", "origin"], cwd=REPO_PATH)
    run(["git", "reset", "--hard", "origin/main"], cwd=REPO_PATH)

    # Step 2: docker compose rebuild
    ok = run(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--build"])

    return {
        "status": "ok" if ok else "error",
        "log": "Update complete, container restarting" if ok else "Build failed",
        "logs": logs,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Static files (web UI) ---

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
    uvicorn.run(app, host="0.0.0.0", port=port)
