import base64
import glob
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gauge_reader import angle_to_value
from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle, detect_scale_range, compute_variance_profile, learn_gap_params
from gauge_reader.value_filter import ValueFilter

CONFIG_PATH = os.environ.get("CONFIG_PATH", "/app/config.json")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown: stop background reader
    _bg_stop.set()
    with _bg_reader_lock:
        if _bg_reader is not None:
            _bg_reader.join(timeout=3)

app = FastAPI(title="Edge Gauge Reader API", lifespan=lifespan)

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
    defaults.setdefault("camera_id", 0)
    defaults.setdefault("cam_resolution", "0x0")
    defaults.setdefault("filter_alpha", 0.15)
    defaults.setdefault("filter_max_jump", 1.5)
    defaults.setdefault("filter_window", 5)
    return defaults


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# --- Camera: single background reader ---
# V4L2 on Orange Pi locks device. Single thread captures frames at
# high speed. Detection is on-demand via /api/one-shot (resized detect).

_frame_buffer = {}         # camera_id -> {"frame": ndarray, "ts": float}

_raw_jpeg_lock = threading.Lock()
_raw_jpeg_cache = {}        # camera_id -> bytes (raw JPEG, Q30, cached per capture)
_frame_buffer_lock = threading.Lock()
_bg_reader = None
_bg_reader_lock = threading.Lock()
_bg_stop = threading.Event()

_detect_config = {}
_detect_config_lock = threading.Lock()
_stream_jpeg = None
_stream_detect = None

_value_filter_lock = threading.Lock()
_value_filter = ValueFilter()

def _reinit_filter(cfg):
    with _value_filter_lock:
        _value_filter.update_params(
            alpha=float(cfg.get("filter_alpha", 0.15)),
            jump=float(cfg.get("filter_max_jump", 1.5)),
        )
        _value_filter.median_window_size = int(cfg.get("filter_window", 5))

_DETECT_MAX_W = 640
_DETECT_USE_W = 320  # internal detection resolution for speed (4× fewer pixels)


def _probe_native_resolution(camera_id):
    try:
        cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            return 640, 480
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return w, h
    except Exception:
        return 640, 480


def _enumerate_cameras(max_check=8):
    devices = []
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
            devices.append({"id": idx, "path": path, "label": f"Video {idx}",
                            "width": w, "height": h,
                            "max_width": mw, "max_height": mh})
    found_ids = {d["id"] for d in devices}
    for idx in range(max_check):
        if idx in found_ids:
            continue
        path = f"/dev/video{idx}"
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
    devices = _enumerate_cameras()
    if not devices:
        cfg = load_config()
        cam_id = int(cfg.get("camera_id", 0))
        mw, mh = _probe_native_resolution(cam_id)
        devices.append({"id": cam_id, "path": f"/dev/video{cam_id}",
                        "label": f"Video {cam_id}",
                        "width": 0, "height": 0,
                        "max_width": mw, "max_height": mh})
    return devices


# --- Background reader ---

def _start_reader(camera_id, width, height):
    global _bg_reader
    with _bg_reader_lock:
        if _bg_reader is not None and _bg_reader.is_alive():
            return
        _bg_stop.clear()
        _bg_reader = threading.Thread(
            target=_reader_loop,
            args=(camera_id, width, height),
            daemon=True,
        )
        _bg_reader.start()


def _reader_loop(camera_id, width, height):
    global _stream_jpeg, _stream_detect
    cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
    if not cap.isOpened():
        return
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FPS, 30)
    # Cap capture to stream max for performance
    if width <= 0 or height <= 0:
        width, height = _DETECT_MAX_W, int(_DETECT_MAX_W * 3 / 4)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    last_detect = 0
    try:
        while not _bg_stop.is_set():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                now = time.time()

                # Invalidate raw JPEG cache — stream re-encodes on demand at Q30
                with _raw_jpeg_lock:
                    _raw_jpeg_cache[camera_id] = None

                if now - last_detect >= 0.2:
                    with _detect_config_lock:
                        cfg = _detect_config.copy() if _detect_config else load_config()
                    if cfg:
                        result = _run_detection(frame, cfg)
                        if not result.get("error"):
                            # Apply value filter
                            with _value_filter_lock:
                                filtered = _value_filter.add(float(result["value"]))
                            result["raw_value"] = result["value"]
                            result["value"] = round(filtered, 2)
                            result["filtered"] = True
                            _stream_detect = result
                            angle_deg = float(result["angle"])
                            ctr = result["center"]
                            annotated = draw_needle(frame.copy(),
                                                    ctr["x"], ctr["y"], ctr["radius"], angle_deg,
                                                    inner_ratio=float(cfg["inner_ratio"]),
                                                    outer_ratio=float(cfg["outer_ratio"]),
                                                    min_angle=float(cfg["min_angle"]),
                                                    max_angle=float(cfg["max_angle"]))
                            _, ann_jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 50])
                            _stream_jpeg = ann_jpeg.tobytes()
                        else:
                            _stream_detect = result
                    last_detect = now

                with _frame_buffer_lock:
                    _frame_buffer[camera_id] = {"frame": frame, "ts": now}
            time.sleep(0.01)
    finally:
        cap.release()
        with _frame_buffer_lock:
            _frame_buffer.pop(camera_id, None)
        _stream_jpeg = None
        _stream_detect = None
        with _raw_jpeg_lock:
            _raw_jpeg_cache.pop(camera_id, None)


def _get_frame(camera_id):
    with _frame_buffer_lock:
        buf = _frame_buffer.get(camera_id)
    if buf is not None and (time.time() - buf["ts"]) < 5.0:
        return buf["frame"]
    return None


# --- MJPEG stream (raw only) ---

def _generate_mjpeg(camera_id, width, height):
    _start_reader(camera_id, width, height)
    try:
        while True:
            if _stream_jpeg is not None:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + _stream_jpeg + b"\r\n")
            else:
                # Encode raw frame on demand at Q30, cache between captures
                with _raw_jpeg_lock:
                    jpeg_bytes = _raw_jpeg_cache.get(camera_id)
                if jpeg_bytes is None:
                    with _frame_buffer_lock:
                        buf = _frame_buffer.get(camera_id)
                    if buf is not None:
                        _, buf2 = cv2.imencode(".jpg", buf["frame"], [cv2.IMWRITE_JPEG_QUALITY, 30])
                        jpeg_bytes = buf2.tobytes()
                        with _raw_jpeg_lock:
                            _raw_jpeg_cache[camera_id] = jpeg_bytes
                if jpeg_bytes is not None:
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n")
                else:
                    time.sleep(0.05)
    except GeneratorExit:
        pass


@app.get("/api/stream")
def stream_video(camera_id: int = Query(0), w: int = Query(0), h: int = Query(0)):
    if w <= 0 or h <= 0:
        w, h = _probe_native_resolution(camera_id)
    return StreamingResponse(
        _generate_mjpeg(camera_id, w, h),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/stream-detect-config")
def set_stream_detect_config(body: dict):
    allowed = {"min_value", "max_value", "min_angle", "max_angle",
               "center_offset_y", "inner_ratio", "outer_ratio",
               "blur_kernel", "threshold_block", "threshold_c",
               "filter_alpha", "filter_max_jump", "filter_window"}
    with _detect_config_lock:
        _detect_config.clear()
        _detect_config.update((k, v) for k, v in body.items() if k in allowed)
    # Reinit filter from detect config (falls back to saved config)
    merged = load_config()
    merged.update(_detect_config)
    _reinit_filter(merged)
    return {"ok": True}


@app.delete("/api/stream-detect-config")
def clear_stream_detect_config():
    with _detect_config_lock:
        _detect_config.clear()
    return {"ok": True}


@app.get("/api/stream-status")
def stream_status():
    if _stream_detect is not None:
        return _stream_detect
    return {"value": None, "angle": None, "center": None}


# --- Detection helpers ---

def _resize_for_detect(img):
    h, w = img.shape[:2]
    if max(w, h) <= _DETECT_MAX_W:
        return img, 1.0
    scale = _DETECT_MAX_W / max(w, h)
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA), 1.0 / scale


def _run_detection(frame, cfg):
    # Detect at _DETECT_USE_W for speed, upscale coords to frame resolution
    h_orig, w_orig = frame.shape[:2]
    if max(w_orig, h_orig) > _DETECT_USE_W:
        scale = _DETECT_USE_W / max(w_orig, h_orig)
        small = cv2.resize(frame, (int(w_orig * scale), int(h_orig * scale)),
                           interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
        small = frame

    center = find_gauge_center(small)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    cy += int(cfg["center_offset_y"])
    angle_deg = find_needle_angle(
        small, cx, cy, radius,
        inner_ratio=float(cfg["inner_ratio"]),
        outer_ratio=float(cfg["outer_ratio"]),
        blur_kernel=int(cfg["blur_kernel"]),
        threshold_block=int(cfg["threshold_block"]),
        threshold_c=int(cfg["threshold_c"]),
    )

    # Upscale coords to original frame resolution
    inv = 1.0 / scale if scale != 1.0 else 1.0
    cx = int(cx * inv)
    cy = int(cy * inv)
    radius = int(radius * inv)

    min_a, max_a = float(cfg["min_angle"]), float(cfg["max_angle"])
    min_v, max_v = float(cfg["min_value"]), float(cfg["max_value"])
    value = angle_to_value(angle_deg, min_a, max_a, min_v, max_v)

    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx, "y": cy, "radius": radius},
        "error": None,
        "w": w_orig, "h": h_orig,
    }


def _finalize_detect_result(result, full_img, upscale, cfg, need_annotation=True):
    ctr = result["center"]
    ctr["x"] = int(ctr["x"] * upscale)
    ctr["y"] = int(ctr["y"] * upscale)
    ctr["radius"] = int(ctr["radius"] * upscale)
    result["center"] = ctr

    h_full, w_full = full_img.shape[:2]
    result["w"] = w_full
    result["h"] = h_full

    if need_annotation:
        angle_deg = float(result["angle"])
        annotated = draw_needle(full_img.copy(),
                                ctr["x"], ctr["y"], ctr["radius"], angle_deg,
                                inner_ratio=float(cfg["inner_ratio"]),
                                outer_ratio=float(cfg["outer_ratio"]),
                                min_angle=float(cfg["min_angle"]),
                                max_angle=float(cfg["max_angle"]))
        _, ann_buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        result["annotated_image"] = base64.b64encode(ann_buf).decode()
    else:
        result["annotated_image"] = None
    return result


# --- One-shot (resized detection, scaled coords) ---

@app.post("/api/one-shot")
def one_shot(
    min_value: float = Form(None),
    max_value: float = Form(None),
    min_angle: float = Form(None),
    max_angle: float = Form(None),
    center_offset_y: float = Form(None),
    inner_ratio: float = Form(None),
    outer_ratio: float = Form(None),
    blur_kernel: int = Form(None),
    threshold_block: int = Form(None),
    threshold_c: int = Form(None),
):
    cfg = load_config()
    # Merge optional overrides
    for k, v in [("min_value", min_value), ("max_value", max_value),
                  ("min_angle", min_angle), ("max_angle", max_angle),
                  ("center_offset_y", center_offset_y),
                  ("inner_ratio", inner_ratio), ("outer_ratio", outer_ratio),
                  ("blur_kernel", blur_kernel),
                  ("threshold_block", threshold_block), ("threshold_c", threshold_c)]:
        if v is not None:
            cfg[k] = v

    cam_id = int(cfg.get("camera_id", 0))
    full = _get_frame(cam_id)
    if full is None:
        raise HTTPException(500, "no frame — start stream first")

    result = _run_detection(full, cfg)
    if result.get("error"):
        return result

    return _finalize_detect_result(result, full, 1.0, cfg)


# --- Auto-calibrate ---

@app.post("/api/auto-calibrate")
async def auto_calibrate(camera_id: int = Form(0), image: UploadFile = File(None)):
    cfg = load_config()
    if image:
        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(500, "failed to decode uploaded image")
    else:
        frame = _get_frame(camera_id)
        if frame is None:
            raise HTTPException(500, "failed to get frame from stream")

    small, _upscale = _resize_for_detect(frame)
    center = find_gauge_center(small)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    point_name = cfg.get("point", "")

    learned = cfg.get("learned_cal", {}).get(point_name, {})
    vr = learned.get("variance_ratio", 0.25)
    mg = learned.get("min_gap_deg", 20)

    result = detect_scale_range(
        small, cx, cy, radius,
        blur_kernel=3,
        threshold_block=0,
        threshold_c=0,
        variance_ratio=vr,
        min_gap_deg=mg,
    )
    if result is None:
        return {"error": "could not detect scale range",
                "min_angle": cfg["min_angle"], "max_angle": cfg["max_angle"]}

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
        "filter_alpha", "filter_max_jump", "filter_window",
    }
    for k, v in body.items():
        if k in allowed:
            cfg[k] = v
    save_config(cfg)
    _reinit_filter(cfg)
    return {"status": "ok", "config": cfg}


@app.get("/api/points")
def proxy_points():
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


# --- Legacy aliases ---

@app.post("/api/test-capture")
def test_capture():
    return one_shot()


@app.post("/api/detect-frame")
def detect_frame(camera_id: int = Form(0)):
    cfg = load_config()
    frame = _get_frame(camera_id)
    if frame is None:
        raise HTTPException(500, "failed to capture frame")
    return _finalize_detect_result(_run_detection(frame, cfg), frame, 1.0, cfg)


# --- External detect endpoint ---

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

    cfg = {
        "center_offset_y": center_offset_y,
        "inner_ratio": inner_ratio,
        "outer_ratio": outer_ratio,
        "blur_kernel": blur_kernel,
        "threshold_block": threshold_block,
        "threshold_c": threshold_c,
        "min_angle": min_angle,
        "max_angle": max_angle,
        "min_value": min_value,
        "max_value": max_value,
    }
    result = _run_detection(img, cfg)
    if result.get("error"):
        return result

    return _finalize_detect_result(result, img, 1.0, cfg, need_annotation=need_annotation)


VERSION_PATH = "/app/version.txt"
REPO_PATH = "/repo"
COMPOSE_FILE = "/repo/edge/docker-compose.yml"


@app.get("/api/version")
def get_version():
    version = "unknown"
    if os.path.exists(VERSION_PATH):
        with open(VERSION_PATH) as f:
            version = f.read().strip()
    return {"version": version, "update_available": False}


@app.post("/api/update")
async def run_update():
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

    run(["git", "fetch", "origin"], cwd=REPO_PATH)
    run(["git", "reset", "--hard", "origin/main"], cwd=REPO_PATH)
    ok = run(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--build"])

    return {"status": "ok" if ok else "error",
            "log": "Update complete" if ok else "Build failed", "logs": logs}


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Static files ---

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
    uvicorn.run(app, host="0.0.0.0", port=port)
