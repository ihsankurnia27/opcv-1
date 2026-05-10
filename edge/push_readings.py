#!/usr/bin/env python3
"""
Scheduled gauge reading pusher.

Reads config.json, captures from camera, detects needle,
and POSTs result to server API on a configurable interval.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

import cv2
import numpy as np

# Make gauge_reader importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gauge_reader import angle_to_value
from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle
from gauge_reader.value_filter import ValueFilter


def load_config(path="config.json"):
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
        "server_api_url": "http://localhost:8082/api/receive_reading.php",
        "api_key": "changeme",
    }
    if os.path.exists(path):
        with open(path) as f:
            defaults.update(json.load(f))
    return defaults


def capture_frame(camera_id=0):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open camera {camera_id}")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError(f"failed to capture frame from camera {camera_id}")
    return frame


_DETECT_USE_W = 320  # internal detection resolution, matches api.py


def detect_gauge(img, config):
    # Resize to _DETECT_USE_W for speed, upscale coords after
    h_orig, w_orig = img.shape[:2]
    if max(w_orig, h_orig) > _DETECT_USE_W:
        scale = _DETECT_USE_W / max(w_orig, h_orig)
        small = cv2.resize(img, (int(w_orig * scale), int(h_orig * scale)),
                             interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
        small = img

    center = find_gauge_center(small)
    if center is None:
        return None, "could not find gauge center"

    cx, cy, radius = center
    cy += int(config["center_offset_y"])
    angle_deg = find_needle_angle(
        small, cx, cy, radius,
        inner_ratio=float(config["inner_ratio"]),
        outer_ratio=float(config["outer_ratio"]),
        blur_kernel=int(config["blur_kernel"]),
        threshold_block=int(config["threshold_block"]),
        threshold_c=int(config["threshold_c"]),
    )

    # Upscale coords to original frame
    inv = 1.0 / scale if scale != 1.0 else 1.0
    cx_out = int(cx * inv)
    cy_out = int(cy * inv)
    radius_out = int(radius * inv)

    value = angle_to_value(angle_deg, float(config["min_angle"]), float(config["max_angle"]),
                           float(config["min_value"]), float(config["max_value"]))

    annotated = draw_needle(img.copy(), cx_out, cy_out, radius_out, angle_deg,
                            inner_ratio=float(config["inner_ratio"]),
                            outer_ratio=float(config["outer_ratio"]),
                            min_angle=float(config["min_angle"]),
                            max_angle=float(config["max_angle"]))
    _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx_out, "y": cy_out, "radius": radius_out},
        "annotated_image": annotated_b64,
    }, None


def push_to_server(payload, config):
    url = config.get("server_api_url", "http://localhost:8082/api/receive_reading.php")
    api_key = config.get("api_key", "")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            return json.loads(body), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"
    except urllib.error.URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)


def do_reading(config, camera_id=0, value_filter=None):
    try:
        frame = capture_frame(camera_id)
    except RuntimeError as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture error: {e}")
        return

    result, err = detect_gauge(frame, config)
    if err or result is None:
        print(f"[{time.strftime('%H:%M:%S')}] Detection error: {err}")
        return

    raw_value = result["value"]
    filtered = value_filter.add(raw_value) if value_filter is not None else raw_value
    if filtered != raw_value:
        print(f"[{time.strftime('%H:%M:%S')}] Spike rejected: {raw_value}→{filtered:.2f}")

    payload = {
        "point": config["point"],
        "value": round(filtered, 2),
        "angle": result["angle"],
        "annotated_image": result["annotated_image"],
    }

    resp, err = push_to_server(payload, config)
    if err:
        print(f"[{time.strftime('%H:%M:%S')}] Push error: {err}")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Pushed {config['point']} = {payload['value']}  server: {resp.get('status', '?')}")


def main():
    parser = argparse.ArgumentParser(description="Periodic gauge reading pusher")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--oneshot", action="store_true", help="Run once and exit")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    args = parser.parse_args()

    config = load_config(args.config)
    interval = config.get("interval_seconds", 3600)

    print(f"Edge pusher started")
    print(f"  Point:      {config['point']}")
    print(f"  Interval:   {interval}s")
    print(f"  Server URL: {config['server_api_url']}")
    print(f"  Camera:     /dev/video{args.camera}")
    print()

    vf = ValueFilter()
    while True:
        do_reading(config, args.camera, value_filter=vf)
        if args.oneshot:
            break
        print(f"  Next reading in {interval}s...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
