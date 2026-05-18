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
from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle_radial import find_needle_angle as find_needle_angle_legacy, draw_needle, detect_scale_range, compute_variance_profile, learn_gap_params
from gauge_reader.find_needle import find_needle_angle
from gauge_reader.preprocess import preprocess
from gauge_reader.temporal import CenterTracker, AngleKalman
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
    defaults.setdefault("detect_method", "auto")
    defaults.setdefault("use_clahe", True)
    defaults.setdefault("use_difference_ref", False)
    defaults.setdefault("overlay_fps", 4)
    defaults.setdefault("center_ema", 0.3)
    defaults.setdefault("angle_kalman_R", 0.1)
    defaults.setdefault("angle_kalman_Q", 0.01)
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
_stream_jpeg = {}          # mode -> ndarray (raw frames)
_stream_detect = None

_value_filter_lock = threading.Lock()
_value_filter = ValueFilter()

_center_tracker = CenterTracker()
_center_tracker_lock = threading.Lock()
_angle_kalman = AngleKalman()
_angle_kalman_lock = threading.Lock()

def _reinit_filter(cfg):
    with _value_filter_lock:
        _value_filter.update_params(
            alpha=float(cfg.get("filter_alpha", 0.15)),
            jump=float(cfg.get("filter_max_jump", 1.5)),
        )
        _value_filter.median_window_size = int(cfg.get("filter_window", 5))

def _reinit_temporal(cfg):
    with _center_tracker_lock:
        _center_tracker.alpha = float(cfg.get("center_ema", 0.3))
    with _angle_kalman_lock:
        _angle_kalman.R = float(cfg.get("angle_kalman_R", 0.1))
        _angle_kalman.Q = float(cfg.get("angle_kalman_Q", 0.01))

_DETECT_MAX_W = 640
_DETECT_USE_W = 480  # internal detection resolution for speed


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
    cap.set(cv2.CAP_PROP_FPS, 60)
    # Only set resolution if explicitly requested, otherwise use camera default to avoid stretching
    if width > 0 and height > 0:
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

                # Update raw and annotated frames every capture iteration for high FPS streaming
                _stream_jpeg["raw"] = frame

                # If we have a recent successful detection, draw overlay on every frame
                if _stream_detect and not _stream_detect.get("error"):
                    with _detect_config_lock:
                        cfg = _detect_config.copy() if _detect_config else load_config()
                    angle_deg = float(_stream_detect["angle"])
                    ctr = _stream_detect["center"]
                    annotated = draw_needle(frame.copy(),
                                            ctr["x"], ctr["y"], ctr["radius"], angle_deg,
                                            inner_ratio=float(cfg["inner_ratio"]),
                                            outer_ratio=float(cfg["outer_ratio"]),
                                            min_angle=float(cfg["min_angle"]),
                                            max_angle=float(cfg["max_angle"]))
                    _stream_jpeg["annotated"] = annotated

                if now - last_detect >= 0.2:
                    with _detect_config_lock:
                        cfg = _detect_config.copy() if _detect_config else load_config()
                    if cfg:
                        try:
                            result = _run_detection(frame, cfg)
                            if not result.get("error"):
                                # Apply value filter
                                with _value_filter_lock:
                                    filtered = _value_filter.add(float(result["value"]))
                                result["raw_value"] = result["value"]
                                result["value"] = round(filtered, 2)
                                result["filtered"] = True

                                # Pull debug images out of result (numpy arrays, not JSON-safe)
                                # Capture them before popping
                                debug_proc_img = result.get("debug_preprocess")
                                debug_bin_img = result.get("debug_binary")
                                debug_proc_ann = result.get("debug_preprocess_ann")
                                debug_bin_ann = result.get("debug_binary_ann")

                                # MUST pop all non-serializable objects before assigning to _stream_detect
                                for k in ["debug_preprocess", "debug_binary", "debug_preprocess_ann", "debug_binary_ann"]:
                                    result.pop(k, None)

                                _stream_detect = result
                                angle_deg = float(result["angle"])
                                ctr = result["center"]

                                # Store frames for on-demand stream encoding
                                # 1. Annotated
                                annotated = draw_needle(frame.copy(),
                                                        ctr["x"], ctr["y"], ctr["radius"], angle_deg,
                                                        inner_ratio=float(cfg["inner_ratio"]),
                                                        outer_ratio=float(cfg["outer_ratio"]),
                                                        min_angle=float(cfg["min_angle"]),
                                                        max_angle=float(cfg["max_angle"]))
                                _stream_jpeg["annotated"] = annotated
                                _stream_jpeg["raw"] = frame

                                # 2. Preprocessed variants
                                if debug_proc_img is not None:
                                    _stream_jpeg["preprocess"] = debug_proc_img
                                    if debug_proc_ann is not None:
                                        _stream_jpeg["preprocess_ann"] = debug_proc_ann

                                # 3. Binary variants
                                if debug_bin_img is not None:
                                    _stream_jpeg["binary"] = debug_bin_img
                                    if debug_bin_ann is not None:
                                        _stream_jpeg["binary_ann"] = debug_bin_ann
                            else:
                                _stream_detect = result
                        except Exception as e:
                            print(f"Reader detection error: {e}")
                            _stream_detect = {"error": str(e)}
                    last_detect = now

                with _frame_buffer_lock:
                    _frame_buffer[camera_id] = {"frame": frame, "ts": now}
            time.sleep(0.01)
    finally:
        cap.release()
        with _frame_buffer_lock:
            _frame_buffer.pop(camera_id, None)
        _stream_jpeg.clear()
        _stream_detect = None
        with _raw_jpeg_lock:
            _raw_jpeg_cache.pop(camera_id, None)


def _get_frame(camera_id):
    with _frame_buffer_lock:
        buf = _frame_buffer.get(camera_id)
    if buf is not None and (time.time() - buf["ts"]) < 5.0:
        return buf["frame"]
    return None


# --- MJPEG stream ---

def _generate_mjpeg(camera_id, width, height, mode="annotated", quality=30, fps=5):
    _start_reader(camera_id, width, height)
    last_frame_time = 0
    try:
        while True:
            now = time.time()
            if now - last_frame_time < (1.0 / fps):
                time.sleep(0.01)
                continue

            # Use requested mode, fallback to annotated
            frame = _stream_jpeg.get(mode)
            if frame is None:
                frame = _stream_jpeg.get("annotated")

            if frame is None:
                # Fallback to buffer if reader haven't populated _stream_jpeg yet
                with _frame_buffer_lock:
                    buf = _frame_buffer.get(camera_id)
                if buf is not None:
                    frame = buf["frame"]

            if frame is not None:
                # Resize if requested resolution differs from frame
                fh, fw = frame.shape[:2]
                if width > 0 and height > 0 and (fw != width or fh != height):
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

                _, buf2 = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                jpeg_bytes = buf2.tobytes()

                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n")
                last_frame_time = now
            else:
                time.sleep(0.1)
    except GeneratorExit:
        pass


@app.get("/api/stream")
def stream_video(camera_id: int = Query(0), w: int = Query(0), h: int = Query(0),
                 mode: str = Query("annotated"), q: int = Query(30), fps: int = Query(5)):
    return StreamingResponse(
        _generate_mjpeg(camera_id, w, h, mode=mode, quality=q, fps=fps),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/stream-detect-config")
def set_stream_detect_config(body: dict):
    allowed = {"min_value", "max_value", "min_angle", "max_angle",
               "center_offset_y", "inner_ratio", "outer_ratio",
               "blur_kernel", "threshold_block", "threshold_c",
               "filter_alpha", "filter_max_jump", "filter_window",
               "detect_method", "use_clahe", "center_ema",
               "angle_kalman_R", "angle_kalman_Q"}
    with _detect_config_lock:
        _detect_config.clear()
        _detect_config.update((k, v) for k, v in body.items() if k in allowed)
    # Reinit filter from detect config (falls back to saved config)
    merged = load_config()
    merged.update(_detect_config)
    _reinit_filter(merged)
    _reinit_temporal(merged)
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
    """Detect gauge: v2 pipeline with legacy fallback via detect_method config."""
    method = cfg.get("detect_method", "auto")
    use_clahe = cfg.get("use_clahe", True)

    h_orig, w_orig = frame.shape[:2]
    if max(w_orig, h_orig) > _DETECT_USE_W:
        scale = _DETECT_USE_W / max(w_orig, h_orig)
        small = cv2.resize(frame, (int(w_orig * scale), int(h_orig * scale)),
                           interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
        small = frame

    # Preprocess
    if method != "radial":
        proc = preprocess(small, clahe=use_clahe, denoise=True)
    else:
        proc = small

    debug_proc = proc.copy()

    # Center detection
    if method == "radial":
        center_result = find_gauge_center_legacy(proc)
        if center_result is None:
            return {"error": "could not find gauge center"}
        cx, cy, radius = center_result
    else:
        with _center_tracker_lock:
            prev = _center_tracker.get() if _center_tracker.initialized else None
        center_result = find_gauge_center(proc, prev_center=prev,
                                          ema_alpha=float(cfg.get("center_ema", 0.3)),
                                          use_clahe=False)
        if center_result is None:
            return {"error": "could not find gauge center"}
        cx, cy, radius = center_result
        with _center_tracker_lock:
            _center_tracker.update(cx, cy, radius)

    cy_adjusted = cy + int(cfg["center_offset_y"])

    # Needle detection
    debug_binary = None
    if method == "radial":
        angle_deg = find_needle_angle_legacy(
            proc, cx, cy_adjusted, radius,
            inner_ratio=float(cfg["inner_ratio"]),
            outer_ratio=float(cfg["outer_ratio"]),
            blur_kernel=int(cfg["blur_kernel"]),
            threshold_block=int(cfg["threshold_block"]),
            threshold_c=int(cfg["threshold_c"]),
        )
    else:
        angle_result = find_needle_angle(
            proc, cx, cy_adjusted, radius,
            inner_ratio=float(cfg["inner_ratio"]),
            outer_ratio=float(cfg["outer_ratio"]),
            blur_kernel=int(cfg["blur_kernel"]),
            threshold_block=int(cfg["threshold_block"]),
            threshold_c=int(cfg["threshold_c"]),
            method=method,
            background_ref=None,
            min_angle=float(cfg["min_angle"]),
            max_angle=float(cfg["max_angle"]),
        )
        if "error" in angle_result:
            return angle_result
        angle_deg = float(angle_result["angle"])

    # Temporal angle filter
    if method != "radial":
        with _angle_kalman_lock:
            angle_deg = _angle_kalman.update(angle_deg)

    # Upscale coords
    inv = 1.0 / scale if scale != 1.0 else 1.0
    cx_out = int(cx * inv)
    cy_out = int(cy_adjusted * inv)
    radius_out = int(radius * inv)

    # Debug images for stream — annotate BEFORE upscaling coords
    gray = cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)
    if int(cfg["blur_kernel"]) > 0:
        k = int(cfg["blur_kernel"])
        k = k if k % 2 == 1 else k + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)

    if int(cfg["threshold_block"]) > 0:
        b = int(cfg["threshold_block"])
        b = b if b % 2 == 1 else b + 1
        debug_binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                             cv2.THRESH_BINARY, b, int(cfg["threshold_c"]))
    else:
        debug_binary = gray

    # Convert debug_proc to grayscale (match what detection sees)
    if debug_proc is not None:
        debug_proc = cv2.cvtColor(debug_proc, cv2.COLOR_BGR2GRAY)

    # Annotate debug images at detection resolution (small-res coords)
    ann_proc = draw_needle(cv2.cvtColor(debug_proc, cv2.COLOR_GRAY2BGR),
                           cx, cy_adjusted, radius, angle_deg,
                           inner_ratio=float(cfg["inner_ratio"]),
                           outer_ratio=float(cfg["outer_ratio"]),
                           min_angle=float(cfg["min_angle"]),
                           max_angle=float(cfg["max_angle"]))
    ann_binary = draw_needle(cv2.cvtColor(debug_binary, cv2.COLOR_GRAY2BGR),
                             cx, cy_adjusted, radius, angle_deg,
                             inner_ratio=float(cfg["inner_ratio"]),
                             outer_ratio=float(cfg["outer_ratio"]),
                             min_angle=float(cfg["min_angle"]),
                             max_angle=float(cfg["max_angle"]))

    min_a, max_a = float(cfg["min_angle"]), float(cfg["max_angle"])
    min_v, max_v = float(cfg["min_value"]), float(cfg["max_value"])
    value = angle_to_value(angle_deg, min_a, max_a, min_v, max_v)

    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx_out, "y": cy_out, "radius": radius_out},
        "error": None,
        "w": w_orig, "h": h_orig,
        "debug_preprocess": debug_proc,
        "debug_binary": debug_binary,
        "debug_preprocess_ann": ann_proc,
        "debug_binary_ann": ann_binary
    }


def _finalize_detect_result(result, full_img, upscale, cfg, need_annotation=True):
    # Strip debug images — numpy arrays not JSON-serializable
    for key in ["debug_preprocess", "debug_binary", "debug_preprocess_ann", "debug_binary_ann"]:
        result.pop(key, None)
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
        "detect_method", "use_clahe", "use_difference_ref",
        "overlay_fps", "center_ema", "angle_kalman_R", "angle_kalman_Q",
    }
    for k, v in body.items():
        if k in allowed:
            cfg[k] = v
    save_config(cfg)
    _reinit_filter(cfg)
    _reinit_temporal(cfg)
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


@app.post("/api/send-to-server")
def send_to_server(
    point: str = Form(...),
    value: float = Form(...),
    angle: float = Form(...),
    annotated_image: str = Form(""),
):
    cfg = load_config()
    url = cfg.get("server_api_url", "")
    if not url:
        raise HTTPException(502, "server_api_url not configured")

    payload = {
        "point": point,
        "value": value,
        "angle": angle,
        "annotated_image": annotated_image,
    }
    api_key = cfg.get("api_key", "")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise HTTPException(502, f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
    except urllib.error.URLError as e:
        raise HTTPException(502, str(e.reason))
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
    detect_method: str = Form("auto"),
    use_clahe: bool = Form(True),
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
        "detect_method": detect_method,
        "use_clahe": use_clahe,
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
