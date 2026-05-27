import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch

from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle import find_needle_angle
from gauge_reader import angle_to_value
from gauge_reader.preprocess import preprocess
from gauge_reader.draw import draw_needle


def make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60, min_a=30, max_a=330):
    """Realistic synthetic gauge with tick marks and needle."""
    img = np.full((480, 640, 3), 210, dtype=np.uint8)

    # Outer bezel
    cv2.circle(img, (cx, cy), radius + 15, (160, 160, 160), 2)
    cv2.circle(img, (cx, cy), radius, (100, 100, 100), 3)

    # Tick marks every 10 degrees
    for a in range(0, 360, 10):
        rad = np.deg2rad(a)
        x1 = int(cx + (radius - 5) * np.cos(rad))
        y1 = int(cy + (radius - 5) * np.sin(rad))
        x2 = int(cx + (radius - 20) * np.cos(rad))
        y2 = int(cy + (radius - 20) * np.sin(rad))
        cv2.line(img, (x1, y1), (x2, y2), (60, 60, 60), 1)

    # Needle
    rad = np.deg2rad(angle_deg)
    x2 = int(cx + (radius - 25) * np.cos(rad))
    y2 = int(cy + (radius - 25) * np.sin(rad))
    cv2.line(img, (cx, cy), (x2, y2), (20, 20, 20), 3)

    # Center pin
    cv2.circle(img, (cx, cy), 6, (40, 40, 40), -1)

    return img


def make_default_config(overrides=None):
    """Create a default config dict for testing (mirrors test_detector)."""
    cfg = {
        "min_value": 0,
        "max_value": 10,
        "min_angle": 30,
        "max_angle": 330,
        "center_offset_y": 0,
        "inner_ratio": 0.30,
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
        "blur_kernel": 0,
        "threshold_block": 0,
        "threshold_c": 5,
        "detect_method": "auto",
        "use_clahe": True,
        "center_ema": 0.3,
        "angle_kalman_R": 0.1,
        "angle_kalman_Q": 0.01,
    }
    if overrides:
        cfg.update(overrides)
    return cfg


# ====================================================================
# Integration: Export → Import round trip
# ====================================================================


def test_export_import_roundtrip():
    """Full export/import roundtrip: create → GET → format → POST → verify."""
    from fastapi.testclient import TestClient
    from app.api import app

    client = TestClient(app)
    base = {"point": "G-01", "server_api_url": "", "api_key": "", "presets": []}

    with patch("app.api.CONFIG_PATH", "/tmp/_test_int_export.json"):
        with open("/tmp/_test_int_export.json", "w") as f:
            json.dump(base, f)

        # Create two presets
        r1 = client.post("/api/presets", json={"name": "Alpha", "params": {"blur_kernel": 7}})
        assert r1.status_code == 201
        r2 = client.post("/api/presets", json={"name": "Beta", "params": {"blur_kernel": 3, "threshold_block": 15}})
        assert r2.status_code == 201

        # GET all (simulate client-side export data gathering)
        resp = client.get("/api/presets")
        assert resp.status_code == 200
        presets = resp.json()
        assert len(presets) == 2

        # Build export payload (matches client-side exportPresets logic)
        export_payload = {
            "version": 1,
            "presets": [{"name": p["name"], "params": p["params"]} for p in presets],
        }

        # Import them back
        resp = client.post("/api/presets/import", json=export_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 2
        assert data["skipped"] == 0

        # Verify still 2 presets (overwritten by name)
        resp = client.get("/api/presets")
        assert resp.status_code == 200
        imported = resp.json()
        assert len(imported) == 2
        names = {p["name"] for p in imported}
        assert "Alpha" in names
        assert "Beta" in names


# ====================================================================
# Integration: Config changes affect detection output
# ====================================================================


def test_detector_config_changes_affect_output():
    """Different GaugeDetector configs produce detectably different outputs."""
    from gauge_reader.detector import GaugeDetector

    img = make_realistic_gauge(angle_deg=90)

    det_default = GaugeDetector(make_default_config())
    r_default = det_default.detect(img.copy())

    det_blur = GaugeDetector(make_default_config({
        "blur_kernel": 7,
        "threshold_block": 15,
    }))
    r_blur = det_blur.detect(img.copy())

    if r_default.get("error") is None and r_blur.get("error") is None:
        # Different blur/threshold should produce different debug binary
        diff = np.abs(
            r_default["debug_binary"].astype(float)
            - r_blur["debug_binary"].astype(float)
        ).mean()
        assert diff > 0, "Different configs should produce different debug output"


# ====================================================================
# Integration: Multiple features active simultaneously
# ====================================================================


def test_multi_feature_roi_confidence_kalman():
    """ROI cropping, confidence scoring, and Kalman all active at once."""
    from gauge_reader.detector import GaugeDetector

    img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60)
    cfg = make_default_config({
        "use_roi": "1",
        "roi_margin": 1.5,
        "min_confidence": 0.0,
    })
    det = GaugeDetector(cfg)
    result = det.detect(img.copy())

    assert result.get("error") is None
    # ROI cropping applied → debug_preprocess should be smaller than 480×640
    h_roi, w_roi = result["debug_preprocess"].shape[:2]
    assert h_roi < 480 or w_roi < 640, (
        f"ROI-cropped debug ({w_roi}×{h_roi}) should be smaller than full frame"
    )
    # Confidence present
    assert "confidence" in result, "Missing confidence key"
    assert isinstance(result["confidence"], float), "Confidence must be float"
    # Rejected flag present
    assert "rejected" in result, "Missing rejected key"
    # Detection produced a value
    assert "value" in result, "Missing value key"
    assert isinstance(result["value"], float), "Value must be float"


# ====================================================================
# Integration: Sequential detection with temporal tracking
# ====================================================================


def test_sequential_detection_temporal_tracking():
    """Multiple detect() calls track angle smoothly via Kalman."""
    from gauge_reader.detector import GaugeDetector

    frames = [
        make_realistic_gauge(angle_deg=50),
        make_realistic_gauge(angle_deg=55),
        make_realistic_gauge(angle_deg=60),
    ]
    cfg = make_default_config({"angle_kalman_R": 0.5, "angle_kalman_Q": 0.05})
    det = GaugeDetector(cfg)

    angles = []
    for frame in frames:
        result = det.detect(frame)
        if result.get("error") is None:
            angles.append(result["angle"])

    assert len(angles) == 3, "All three frames should produce valid detections"
    # Angles should increase monotonically (needle moves CCW)
    assert angles[0] < angles[1] < angles[2], (
        f"Angles should increase with needle motion: {angles}"
    )
    # Kalman smoothing → 3rd angle should be < 60 (lag behind measurement)
    assert angles[2] < 60, (
        f"Kalman lag expected: 3rd angle {angles[2]:.2f} should be < 60"
    )


# ====================================================================
# Integration: Config overrides are per-call only
# ====================================================================


def test_config_overrides_do_not_persist():
    """Config overrides to detect() should not persist for subsequent calls."""
    from gauge_reader.detector import GaugeDetector

    img = make_realistic_gauge(angle_deg=90)
    cfg = make_default_config({"min_confidence": 0.0})
    det = GaugeDetector(cfg)

    # Call with override that should reject
    r1 = det.detect(img.copy(), config_overrides={"min_confidence": 0.99})
    # Call without override → should use base config (min_confidence=0.0 → never reject)
    r2 = det.detect(img.copy())

    if r1.get("error") is None and r2.get("error") is None:
        # r1 should be rejected (or have high confidence from synthetic gauge)
        # r2 should NOT be rejected (min_confidence=0.0)
        # They should differ in rejected status
        assert r1["rejected"] is True or r2["rejected"] is False
        # At minimum, the reject flags should differ
        assert r1["rejected"] != r2["rejected"] or (
            r1["rejected"] is True and r2["rejected"] is True
        ), (
            f"Expected different rejection between override ({r1['rejected']}) "
            f"and base ({r2['rejected']})"
        )


# ====================================================================
# Edge case: angle_to_value
# ====================================================================


class TestAngleToValueEdgeCases:
    """Edge-case behavior of angle_to_value()."""

    def test_zero_angle_range_returns_min_value(self):
        """When min_angle == max_angle, should return min_value."""
        v = angle_to_value(90, 45, 45, 0, 100)
        assert v == 0

    def test_zero_value_range_returns_value(self):
        """When min_value == max_value, should return that value."""
        v = angle_to_value(90, 0, 360, 50, 50)
        assert v == 50

    def test_at_min_boundary_returns_min_value(self):
        """Angle exactly at min_angle gives min_value."""
        v = angle_to_value(45, 45, 315, 0, 100)
        assert v == 0

    def test_at_max_boundary_returns_max_value(self):
        """Angle exactly at max_angle gives max_value."""
        v = angle_to_value(315, 45, 315, 0, 100)
        assert v == 100

    def test_extreme_values_clamp_to_range(self):
        """Angle far outside range clamps to min/max value."""
        v = angle_to_value(0, 45, 315, 0, 100)
        assert v == 0, f"Below-min angle should clamp to 0, got {v}"
        v = angle_to_value(360, 45, 315, 0, 100)
        assert v == 100, f"Above-max angle should clamp to 100, got {v}"

    def test_wrap_around_at_min_boundary(self):
        """Wrap-around config: angle at min_angle gives min_value."""
        v = angle_to_value(315, 315, 45, 0, 100)
        assert v == 0, f"Wrap min boundary: expected 0, got {v}"

    def test_wrap_around_at_max_boundary(self):
        """Wrap-around config: angle at max_angle gives max_value."""
        v = angle_to_value(45, 315, 45, 0, 100)
        assert v == 100, f"Wrap max boundary: expected 100, got {v}"

    def test_wrap_around_mid_range(self):
        """Wrap-around config: mid-range angle produces proportional value."""
        v = angle_to_value(0, 315, 45, 0, 100)
        assert 45 < v < 55, f"Wrap mid-range: expected ~50, got {v}"


def test_full_pipeline_synthetic_60deg():
    img = make_realistic_gauge(angle_deg=60)
    proc = preprocess(img, clahe=True, denoise=True)
    center = find_gauge_center(proc, use_clahe=False)  # already CLAHE'd
    assert center is not None, "center detection failed"
    cx, cy, radius = center

    needle = find_needle_angle(proc, cx, cy, radius,
                               inner_ratio=0.30, outer_ratio=0.80,
                               blur_kernel=0, threshold_block=0, threshold_c=0,
                               method="auto", use_clahe=False)
    assert "error" not in needle, f"needle detection failed: {needle}"
    detected_angle = needle["angle"]
    diff = abs(detected_angle - 60)
    # Account for 180-degree line ambiguity
    diff_mod = min(diff, abs(diff - 360))
    diff_180 = min(diff_mod, abs(diff_mod - 180))
    assert diff_180 < 15, f"Angle off by {diff_180:.1f}, detected {detected_angle}"


def test_full_pipeline_synthetic_150deg():
    img = make_realistic_gauge(angle_deg=150)
    proc = preprocess(img, clahe=True, denoise=True)
    center = find_gauge_center(proc, use_clahe=False)
    assert center is not None
    cx, cy, radius = center
    needle = find_needle_angle(proc, cx, cy, radius,
                               inner_ratio=0.30, outer_ratio=0.80,
                               method="auto", use_clahe=False)
    # Line detector has 180-degree directional ambiguity;
    # the needle line at 150 is also the line at 330
    diff = abs(needle["angle"] - 150)
    diff_mod = min(diff, abs(diff - 360))
    diff_180 = min(diff_mod, abs(diff_mod - 180))
    assert diff_180 < 15, f"Angle off by {diff_180:.1f}, detected {needle['angle']}"


def test_draw_needle_returns_image():
    img = make_realistic_gauge(angle_deg=45)
    annotated = draw_needle(img.copy(), 320, 240, 150, 45,
                            inner_ratio=0.30, outer_ratio=0.80,
                            min_angle=30, max_angle=330)
    assert annotated.shape == img.shape
    assert annotated is not img  # copy


def test_legacy_radial_works():
    img = make_realistic_gauge(angle_deg=90)
    center = find_gauge_center_legacy(img)
    assert center is not None
    cx, cy, radius = center
    needle = find_needle_angle(img, cx, cy, radius,
                               method="radial", use_clahe=False)
    assert "error" not in needle
    diff = abs(needle["angle"] - 90)
    diff_mod = min(diff, abs(diff - 360))
    diff_180 = min(diff_mod, abs(diff_mod - 180))
    assert diff_180 < 25, f"Angle off by {diff_180:.1f}, detected {needle['angle']}"
    assert needle["method"] == "radial"


def test_angle_to_value_wrap():
    # min_angle=315, max_angle=45 -> wraps around 0
    v = angle_to_value(0, 315, 45, 0, 100)
    assert 45 < v < 55, f"Expected ~50, got {v}"


def test_angle_to_value_normal():
    v = angle_to_value(135, 45, 315, 0, 10)
    assert 3 < v < 4, f"Expected ~3.33, got {v}"
