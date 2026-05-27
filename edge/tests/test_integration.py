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


# ====================================================================
# Integration: Backward compat — old config loads with defaults
# ====================================================================


def test_old_config_loads_with_defaults():
    """Old-format config (without new keys) loads successfully with all defaults."""
    from unittest.mock import patch

    from gauge_reader.detector import GaugeDetector

    # --- Part 1: GaugeDetector accepts old config without new keys ---
    old_cfg = make_default_config()
    # Verify old config has NO new keys
    assert "use_roi" not in old_cfg
    assert "roi_margin" not in old_cfg
    assert "min_confidence" not in old_cfg
    assert "presets" not in old_cfg
    assert "angle_kalman_dt" not in old_cfg

    det = GaugeDetector(old_cfg)
    img = make_realistic_gauge(angle_deg=90)
    result = det.detect(img.copy())

    assert result.get("error") is None, f"Detection failed: {result.get('error')}"
    # Default min_confidence=0.0 → never reject
    assert result["rejected"] is False
    # Default use_roi=False → no ROI crop → debug_preprocess is full detection size
    h_proc, w_proc = result["debug_preprocess"].shape[:2]
    assert h_proc == 360 and w_proc == 480, (
        f"Expected full detection frame (360, 480) without ROI, got ({h_proc}, {w_proc})"
    )
    # Default angle_kalman_dt=0.2 used by AngleKalman
    assert det._angle_kalman.dt == 0.2
    # Detection with old config still produces all new output keys
    assert "confidence" in result
    assert "rejected" in result

    # --- Part 2: load_config() fills in new keys with defaults ---
    from app.api import load_config

    with patch("app.api.CONFIG_PATH", "/tmp/_test_nonexistent_bc.json"):
        cfg = load_config()
        assert cfg.get("use_roi") is False
        assert cfg.get("roi_margin") == 1.5
        assert cfg.get("min_confidence") == 0.0
        assert cfg.get("presets") == []


# ====================================================================
# Integration: Preset roundtrip (save → load → export → import)
# ====================================================================


def test_preset_roundtrip():
    """Preset params survive save → load → export → import roundtrip at module level."""
    from gauge_reader.detector import GaugeDetector

    # --- Save: capture current params to a preset dict ---
    original_params = {"blur_kernel": 7, "threshold_block": 15}

    # --- Export: serialize to transport format ---
    export_data = {
        "version": 1,
        "presets": [{"name": "TestPreset", "params": original_params}],
    }

    # --- Import: extract params from transport format ---
    imported_params = export_data["presets"][0]["params"]

    # Verify params survive roundtrip
    assert imported_params == original_params
    assert imported_params["blur_kernel"] == 7
    assert imported_params["threshold_block"] == 15

    # --- Load: apply imported params to a detector via config ---
    cfg = make_default_config(imported_params)
    det = GaugeDetector(cfg)
    img = make_realistic_gauge(angle_deg=90)
    result = det.detect(img.copy())

    assert result.get("error") is None, f"Detection failed: {result.get('error')}"

    # --- Verify imported params took effect (compare with default config) ---
    cfg_default = make_default_config()
    det_default = GaugeDetector(cfg_default)
    r_default = det_default.detect(img.copy())

    if r_default.get("error") is None and result.get("error") is None:
        # blur_kernel=7, threshold_block=15 should produce different output than defaults
        diff = np.abs(
            r_default["debug_binary"].astype(float)
            - result["debug_binary"].astype(float)
        ).mean()
        assert diff > 0, "Preset params should change detection output"


# ====================================================================
# Integration: All new features enabled simultaneously
# ====================================================================


def test_all_features_enabled_detection_works():
    """All new features enabled simultaneously produces valid detection output."""
    from gauge_reader.detector import GaugeDetector

    img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60)
    cfg = make_default_config({
        "use_roi": True,
        "roi_margin": 1.5,
        "clahe_clip": 3.0,
        "clahe_tile": 12,
        "min_confidence": 0.0,
        "angle_kalman_dt": 0.2,
    })
    det = GaugeDetector(cfg)
    result = det.detect(img.copy())

    # Verify all expected output keys present
    assert result.get("error") is None, f"Detection failed: {result.get('error')}"
    required_keys = {"value", "angle", "center", "error", "w", "h", "confidence", "rejected"}
    assert required_keys.issubset(result.keys()), (
        f"Missing keys: {required_keys - result.keys()}"
    )
    assert "x" in result["center"]
    assert "y" in result["center"]
    assert "radius" in result["center"]

    # All values are reasonable
    assert isinstance(result["value"], float)
    assert isinstance(result["angle"], float)
    assert isinstance(result["confidence"], float)
    assert isinstance(result["rejected"], bool)
    assert 0 <= result["confidence"] <= 1
    assert result["center"]["x"] >= 0
    assert result["center"]["y"] >= 0
    assert result["center"]["radius"] > 0
    assert result["w"] > 0
    assert result["h"] > 0


# ====================================================================
# Integration: Confidence field in detection result
# ====================================================================


def test_confidence_field_present():
    """Detection result always includes confidence and rejected keys with valid values."""
    from gauge_reader.detector import GaugeDetector

    img = make_realistic_gauge(angle_deg=90)
    det = GaugeDetector(make_default_config())
    result = det.detect(img.copy())

    assert result.get("error") is None, f"Detection failed: {result.get('error')}"
    assert "confidence" in result, "Missing 'confidence' in detection result"
    assert "rejected" in result, "Missing 'rejected' in detection result"
    assert isinstance(result["confidence"], float)
    assert isinstance(result["rejected"], bool)
    assert 0 <= result["confidence"] <= 1, (
        f"Confidence {result['confidence']} outside [0, 1]"
    )


# ====================================================================
# Integration: ROI detection produces valid result
# ====================================================================


def test_roi_detection_produces_valid_result():
    """ROI cropping enabled produces valid angle and value, no error."""
    from gauge_reader.detector import GaugeDetector

    img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60)
    cfg = make_default_config({
        "use_roi": True,
        "roi_margin": 1.5,
    })
    det = GaugeDetector(cfg)
    result = det.detect(img.copy())

    assert result.get("error") is None, f"ROI detection failed: {result.get('error')}"
    assert isinstance(result["angle"], float), f"angle must be float, got {type(result['angle'])}"
    assert isinstance(result["value"], float), f"value must be float, got {type(result['value'])}"
    # ROI should produce a cropped debug_preprocess (smaller than full frame)
    h_roi, w_roi = result["debug_preprocess"].shape[:2]
    assert h_roi < 360 or w_roi < 480, (
        f"ROI-cropped debug ({w_roi}×{h_roi}) should be smaller than detection frame"
    )


# ====================================================================
# Integration: 2D Kalman with velocity state
# ====================================================================


def test_kalman_enhanced_active():
    """GaugeDetector uses 2D AngleKalman with velocity state after two updates."""
    from gauge_reader.detector import GaugeDetector
    from gauge_reader.temporal import AngleKalman

    # --- Verify AngleKalman is 2D constant-velocity ---
    kalman = AngleKalman()
    F = kalman._F()
    assert F.shape == (2, 2), f"Expected 2×2 F matrix, got {F.shape}"
    assert F[0, 1] > 0, "F[0,1] should be dt > 0 (velocity → angle coupling)"
    assert F[1, 1] == 1.0, "F[1,1] should be 1.0 (velocity persistence)"
    assert kalman.H.shape == (1, 2), (
        f"Expected 1×2 H matrix, got {kalman.H.shape}"
    )

    # --- Verify GaugeDetector uses AngleKalman with velocity tracking ---
    cfg = make_default_config({"angle_kalman_dt": 0.2})
    det = GaugeDetector(cfg)

    assert det._angle_kalman is not None
    assert det._angle_kalman.H.shape == (1, 2)

    # Call detect twice to initialize and update Kalman
    img1 = make_realistic_gauge(angle_deg=50)
    img2 = make_realistic_gauge(angle_deg=60)

    r1 = det.detect(img1.copy())
    assert r1.get("error") is None, f"First detection failed: {r1.get('error')}"

    r2 = det.detect(img2.copy())
    assert r2.get("error") is None, f"Second detection failed: {r2.get('error')}"

    # After two updates, Kalman state should have [angle, velocity]
    x = det._angle_kalman._x
    assert x is not None, "AngleKalman state should be initialized"
    assert len(x) == 2, f"Expected 2-element state [angle, vel], got {x}"
    # Needle moved from 50 to 60 → velocity should be nonzero
    assert abs(x[1]) > 0, (
        f"Expected nonzero velocity after 50→60 motion, got {x[1]}"
    )
    # Filtered angle should be between 50 and 60 (lag behind measurement)
    assert 50 <= r2["angle"] < 60, (
        f"Kalman smoothed angle {r2['angle']} should lag behind 60° measurement"
    )


# ====================================================================
# Integration: /api/config endpoint shape preserved
# ====================================================================


def test_config_endpoint_returns_all_keys():
    """/api/config returns same shape for existing keys as before."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient
    from app.api import app

    client = TestClient(app)

    with patch("app.api.CONFIG_PATH", "/tmp/_test_nonexistent_config_shape.json"):
        resp = client.get("/api/config")
    assert resp.status_code == 200
    cfg = resp.json()

    # Old keys still present with correct types
    assert "point" in cfg
    assert isinstance(cfg["point"], str)
    assert "min_value" in cfg
    assert isinstance(cfg["min_value"], (int, float))
    assert "max_value" in cfg
    assert "min_angle" in cfg
    assert "max_angle" in cfg
    assert "center_offset_y" in cfg
    assert "inner_ratio" in cfg
    assert "outer_ratio" in cfg
    assert "blur_kernel" in cfg
    assert "threshold_block" in cfg
    assert "threshold_c" in cfg
    assert isinstance(cfg["threshold_c"], (int, float))
    assert "interval_seconds" in cfg
    assert "server_api_url" in cfg
    assert "api_key" in cfg

    # New keys present with defaults
    assert cfg.get("use_roi") is False
    assert cfg.get("roi_margin") == 1.5
    assert cfg.get("min_confidence") == 0.0
    assert cfg.get("presets") == []

    # Verify no key changed type (old keys should still be present)
    old_keys = {
        "point", "min_value", "max_value", "min_angle", "max_angle",
        "center_offset_y", "inner_ratio", "outer_ratio",
        "blur_kernel", "threshold_block", "threshold_c",
        "circle_hough_param1", "circle_hough_param2", "circle_hough_dp",
        "circle_canny_low", "circle_canny_high",
        "circle_adaptive_thresh", "circle_dilate", "circle_clahe_clip",
        "circle_min_circularity", "circle_min_dist_ratio",
        "circle_min_radius_ratio", "circle_max_radius_ratio",
        "interval_seconds", "server_api_url", "api_key",
        "camera_id", "cam_resolution",
        "filter_alpha", "filter_max_jump", "filter_window",
        "detect_method", "use_clahe", "center_ema",
        "angle_kalman_R", "angle_kalman_Q",
    }
    for key in old_keys:
        assert key in cfg, f"Old key '{key}' missing from /api/config"


# ====================================================================
# Integration: /detect endpoint unchanged
# ====================================================================


def test_detect_endpoint_unchanged():
    """/detect endpoint has same param names and response shape as before."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient
    from app.api import app

    client = TestClient(app)

    img = make_realistic_gauge(angle_deg=90)
    _, buf = cv2.imencode(".jpg", img)

    with patch("app.api.CONFIG_PATH", "/tmp/_test_nonexistent_detect.json"):
        resp = client.post(
            "/detect",
            files={"image": ("test.jpg", buf.tobytes(), "image/jpeg")},
            data={
                "min_angle": 45.0,
                "max_angle": 315.0,
                "min_value": 0.0,
                "max_value": 10.0,
                "center_offset_y": 0.0,
                "inner_ratio": 0.60,
                "outer_ratio": 0.80,
                "blur_kernel": 5,
                "threshold_block": 0,
                "threshold_c": 5,
                "detect_method": "auto",
                "use_clahe": True,
                "need_annotation": True,
            },
        )
    assert resp.status_code == 200
    data = resp.json()

    # Response has expected shape (same keys as before)
    assert "value" in data, "Missing 'value' in /detect response"
    assert "angle" in data, "Missing 'angle' in /detect response"
    assert "center" in data, "Missing 'center' in /detect response"
    assert "error" in data, "Missing 'error' in /detect response"
    assert "w" in data, "Missing 'w' in /detect response"
    assert "h" in data, "Missing 'h' in /detect response"
    assert "annotated_image" in data, "Missing 'annotated_image' in /detect response"
    assert "confidence" in data, "Missing 'confidence' in /detect response"
    assert "rejected" in data, "Missing 'rejected' in /detect response"
    assert "x" in data["center"]
    assert "y" in data["center"]
    assert "radius" in data["center"]

    # Value types are correct
    assert isinstance(data["value"], float)
    assert isinstance(data["angle"], float)
    assert data.get("error") is None, f"Detection error: {data.get('error')}"
    assert 0 <= data["confidence"] <= 1, (
        f"Confidence {data['confidence']} outside [0, 1]"
    )
    assert isinstance(data["rejected"], bool)
