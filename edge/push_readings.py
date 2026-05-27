#!/usr/bin/env python3
"""
Scheduled gauge reading pusher.

Reads config.json, captures from camera, detects needle,
and POSTs result to server API on a configurable interval.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

import cv2

# Make gauge_reader importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gauge_reader.detector import GaugeDetector
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


def do_reading(config, camera_id=0, value_filter=None, detector=None):
    try:
        frame = capture_frame(camera_id)
    except RuntimeError as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture error: {e}")
        return

    assert detector is not None, "GaugeDetector required"
    result = detector.detect(frame)
    if result.get("error"):
        print(f"[{time.strftime('%H:%M:%S')}] Detection error: {result['error']}")
        return

    raw_value = result["value"]
    filtered = value_filter.add(raw_value) if value_filter is not None else raw_value
    if filtered != raw_value:
        print(f"[{time.strftime('%H:%M:%S')}] Spike rejected: {raw_value}→{filtered:.2f}")

    # Produce annotated image for the push payload
    finalized = detector.finalize_result(result, frame, 1.0, config)

    payload = {
        "point": config["point"],
        "value": round(filtered, 2),
        "angle": finalized["angle"],
        "annotated_image": finalized["annotated_image"],
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
    detector = GaugeDetector(config)
    while True:
        do_reading(config, args.camera, value_filter=vf, detector=detector)
        if args.oneshot:
            break
        print(f"  Next reading in {interval}s...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
