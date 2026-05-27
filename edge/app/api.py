import base64
import glob
import json
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime
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

from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import draw_needle, detect_scale_range, compute_variance_profile, learn_gap_params
from gauge_reader.temporal import CenterTracker, AngleKalman
from gauge_reader.value_filter import ValueFilter
from gauge_reader.detector import GaugeDetector

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
        "circle_hough_param1": 100,
        "circle_hough_param2": 50,
        "circle_hough_dp": 1.2,
        "circle_canny_low": 50,
        "circle_canny_high": 150,
        "circle_adaptive_thresh": False,
        "circle_dilate": 0,
        "circle_clahe_clip": 2.0,
        "circle_min_circularity": 0.7,
        "circle_min_dist_ratio": 0.3,
        "circle_min_radius_ratio": 0.05,
        "circle_max_radius_ratio": 0.45,
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
    # V4L2 camera controls
    defaults.setdefault("cam_brightness", -1)
    defaults.setdefault("cam_contrast", -1)
    defaults.setdefault("cam_gain", -1)
    defaults.setdefault("cam_auto_exposure", True)
    defaults.setdefault("cam_exposure_absolute", -1)
    defaults.setdefault("presets", [])
    defaults.setdefault("use_roi", False)
    defaults.setdefault("roi_margin", 1.5)
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

# Keys allowed for runtime detection config overrides (stream-detect-config + presets)
ALLOWED_DETECT_KEYS = {
    "min_value", "max_value", "min_angle", "max_angle",
    "center_offset_y", "inner_ratio", "outer_ratio",
    "circle_hough_param1", "circle_hough_param2", "circle_hough_dp",
    "circle_canny_low", "circle_canny_high",
    "circle_adaptive_thresh", "circle_dilate", "circle_clahe_clip",
    "circle_min_circularity", "circle_min_dist_ratio",
    "circle_min_radius_ratio", "circle_max_radius_ratio",
    "blur_kernel", "threshold_block", "threshold_c",
    "filter_alpha", "filter_max_jump", "filter_window",
    "detect_method", "use_clahe", "center_ema",
    "angle_kalman_R", "angle_kalman_Q", "angle_kalman_dt",
    "use_roi", "roi_margin",
}

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

_gauge_detector = None
_gauge_detector_lock = threading.Lock()


def _get_gauge_detector():
    """Lazy-init GaugeDetector, sharing temporal state."""
    global _gauge_detector
    if _gauge_detector is not None:
        return _gauge_detector
    with _gauge_detector_lock:
        if _gauge_detector is None:
            _gauge_detector = GaugeDetector(
                load_config(),
                center_tracker=_center_tracker,
                angle_kalman=_angle_kalman,
                center_tracker_lock=_center_tracker_lock,
                angle_kalman_lock=_angle_kalman_lock,
            )
    return _gauge_detector

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
        _angle_kalman.set_measurement_noise(float(cfg.get("angle_kalman_R", 0.1)))
        _angle_kalman.set_process_noise(Q_angle=float(cfg.get("angle_kalman_Q", 0.01)))
        _angle_kalman.set_dt(float(cfg.get("angle_kalman_dt", 0.2)))

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

    # Apply V4L2 controls from config
    cfg = load_config()
    brightness = int(cfg.get("cam_brightness", -1))
    if brightness >= 0:
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    contrast = int(cfg.get("cam_contrast", -1))
    if contrast >= 0:
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    gain = int(cfg.get("cam_gain", -1))
    if gain >= 0:
        cap.set(cv2.CAP_PROP_GAIN, gain)
    auto_exp = cfg.get("cam_auto_exposure", True)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1 if auto_exp else 0)
    exposure = int(cfg.get("cam_exposure_absolute", -1))
    if exposure >= 0:
        cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

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
    with _detect_config_lock:
        _detect_config.clear()
        _detect_config.update((k, v) for k, v in body.items() if k in ALLOWED_DETECT_KEYS)
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
    """Detect gauge — backward-compat wrapper.  Delegates to GaugeDetector."""
    return _get_gauge_detector()._run_detection(frame, cfg)


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
    circle_hough_param1: float = Form(None),
    circle_hough_param2: float = Form(None),
    circle_canny_low: int = Form(None),
    circle_canny_high: int = Form(None),
    circle_adaptive_thresh: bool = Form(None),
    circle_dilate: int = Form(None),
    circle_clahe_clip: float = Form(None),
    use_roi: bool = Form(None),
    roi_margin: float = Form(None),
):
    cfg = load_config()
    # Merge optional overrides
    for k, v in [("min_value", min_value), ("max_value", max_value),
                  ("min_angle", min_angle), ("max_angle", max_angle),
                  ("center_offset_y", center_offset_y),
                  ("inner_ratio", inner_ratio), ("outer_ratio", outer_ratio),
                  ("blur_kernel", blur_kernel),
                  ("threshold_block", threshold_block), ("threshold_c", threshold_c),
                  ("circle_hough_param1", circle_hough_param1),
                  ("circle_hough_param2", circle_hough_param2),
                  ("circle_canny_low", circle_canny_low),
                  ("circle_canny_high", circle_canny_high),
                  ("circle_adaptive_thresh", circle_adaptive_thresh),
                  ("circle_dilate", circle_dilate),
                  ("circle_clahe_clip", circle_clahe_clip),
                  ("use_roi", use_roi),
                  ("roi_margin", roi_margin)]:
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


@app.get("/api/debug-frame")
def debug_frame():
    """Debug: save current frame buffer to /tmp for analysis."""
    for cam_id, buf in _frame_buffer.items():
        f = buf["frame"]
        path = f"/tmp/debug_frame_cam{cam_id}.jpg"
        cv2.imwrite(path, f, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return {"saved": path, "shape": list(f.shape), "mean": float(f.mean()), "age": time.time() - buf["ts"]}
    return {"error": "no frame buffer"}


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
        "circle_hough_param1", "circle_hough_param2", "circle_hough_dp",
        "circle_canny_low", "circle_canny_high",
        "circle_adaptive_thresh", "circle_dilate", "circle_clahe_clip",
        "circle_min_circularity", "circle_min_dist_ratio",
        "circle_min_radius_ratio", "circle_max_radius_ratio",
        "blur_kernel", "threshold_block", "threshold_c",
        "interval_seconds", "server_api_url", "api_key",
        "filter_alpha", "filter_max_jump", "filter_window",
        "detect_method", "use_clahe", "use_difference_ref",
        "overlay_fps", "center_ema", "angle_kalman_R", "angle_kalman_Q", "angle_kalman_dt",
        "cam_brightness", "cam_contrast", "cam_gain",
        "cam_auto_exposure", "cam_exposure_absolute",
        "use_roi", "roi_margin",
    }
    for k, v in body.items():
        if k in allowed:
            cfg[k] = v
    save_config(cfg)
    _reinit_filter(cfg)
    _reinit_temporal(cfg)
    return {"status": "ok", "config": cfg}


# --- Presets CRUD ---

def _find_preset(presets, pid):
    for i, p in enumerate(presets):
        if p.get("id") == pid:
            return i, p
    return None, None


@app.get("/api/presets")
def list_presets():
    cfg = load_config()
    return cfg.get("presets", [])


@app.post("/api/presets", status_code=201)
def create_preset(body: dict):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "name is required")
    cfg = load_config()
    presets = cfg.setdefault("presets", [])
    params = body.get("params", {})
    for p in presets:
        if p.get("name") == name:
            p["params"] = params
            p["id"] = uuid.uuid4().hex[:12]
            p["created"] = datetime.now().isoformat()
            save_config(cfg)
            return p
    preset = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "params": params,
        "created": datetime.now().isoformat(),
    }
    presets.append(preset)
    save_config(cfg)
    return preset


@app.get("/api/presets/{pid}")
def get_preset(pid: str):
    cfg = load_config()
    _, p = _find_preset(cfg.get("presets", []), pid)
    if p is None:
        raise HTTPException(404, "preset not found")
    return p


@app.put("/api/presets/{pid}")
def update_preset(pid: str, body: dict):
    cfg = load_config()
    presets = cfg.get("presets", [])
    i, p = _find_preset(presets, pid)
    if p is None:
        raise HTTPException(404, "preset not found")
    if "name" in body and body["name"].strip():
        p["name"] = body["name"].strip()
    if "params" in body:
        p["params"] = body["params"]
    presets[i] = p
    save_config(cfg)
    return p


@app.delete("/api/presets/{pid}", status_code=204)
def delete_preset(pid: str):
    cfg = load_config()
    presets = cfg.get("presets", [])
    i, p = _find_preset(presets, pid)
    if p is None:
        raise HTTPException(404, "preset not found")
    presets.pop(i)
    save_config(cfg)


@app.post("/api/presets/{pid}/apply")
def apply_preset(pid: str):
    cfg = load_config()
    _, p = _find_preset(cfg.get("presets", []), pid)
    if p is None:
        raise HTTPException(404, "preset not found")
    with _detect_config_lock:
        for k, v in p.get("params", {}).items():
            if k in ALLOWED_DETECT_KEYS:
                _detect_config[k] = v
    merged = load_config()
    merged.update(_detect_config)
    _reinit_filter(merged)
    _reinit_temporal(merged)
    return {"ok": True}


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
    circle_canny_low: int = Form(50),
    circle_canny_high: int = Form(150),
    circle_adaptive_thresh: bool = Form(False),
    circle_dilate: int = Form(0),
    circle_clahe_clip: float = Form(2.0),
    need_annotation: bool = Form(True),
    detect_method: str = Form("auto"),
    use_clahe: bool = Form(True),
    use_roi: bool = Form(False),
    roi_margin: float = Form(1.5),
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
        "circle_canny_low": circle_canny_low,
        "circle_canny_high": circle_canny_high,
        "circle_adaptive_thresh": circle_adaptive_thresh,
        "circle_dilate": circle_dilate,
        "circle_clahe_clip": circle_clahe_clip,
        "min_angle": min_angle,
        "max_angle": max_angle,
        "min_value": min_value,
        "max_value": max_value,
        "detect_method": detect_method,
        "use_clahe": use_clahe,
        "use_roi": use_roi,
        "roi_margin": roi_margin,
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
