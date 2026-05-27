"""TDD tests for GaugeDetector refactoring.

These tests verify the GaugeDetector class exists and produces
the same behavior as the original inline detection code.
"""

import numpy as np
import cv2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60,
                         min_a=30, max_a=330):
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
    """Create a default config dict for testing."""
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


# ============================================================
# RED tests — GaugeDetector does NOT exist yet, these will fail
# ============================================================


class TestGaugeDetectorExists:
    """Test that GaugeDetector class and its public API exist."""

    def test_can_import(self):
        from gauge_reader.detector import GaugeDetector
        assert GaugeDetector is not None

    def test_can_instantiate(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        assert det is not None

    def test_detect_method_exists(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        assert hasattr(det, 'detect')
        assert callable(det.detect)

    def test_resize_for_detect_method_exists(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        assert hasattr(det, 'resize_for_detect')
        assert callable(det.resize_for_detect)

    def test_finalize_result_method_exists(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        assert hasattr(det, 'finalize_result')
        assert callable(det.finalize_result)


class TestGaugeDetectorDetect:
    """Test detect() output format and correctness."""

    def test_detect_returns_dict(self):
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        assert isinstance(result, dict)

    def test_detect_has_expected_keys(self):
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        expected_keys = {"value", "angle", "center", "error",
                         "w", "h",
                         "debug_preprocess", "debug_binary",
                         "debug_preprocess_ann", "debug_binary_ann"}
        for k in expected_keys:
            assert k in result, f"Missing key: {k}"

    def test_detect_angle_close_to_ground_truth(self):
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=60)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        assert result.get("error") is None, f"Detection error: {result.get('error')}"
        detected = float(result["angle"])
        diff = abs(detected - 60)
        diff_mod = min(diff, abs(diff - 360))
        diff_180 = min(diff_mod, abs(diff_mod - 180))
        assert diff_180 < 15, f"Angle off by {diff_180:.1f}, detected {detected}"

    def test_detect_with_config_overrides(self):
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=150)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img, config_overrides={"blur_kernel": 3})
        assert isinstance(result, dict)
        # Should not error even with overrides
        assert result.get("error") is None or result.get("error") == ""

    def test_detect_center_is_dict_with_xy_radius(self):
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            ctr = result["center"]
            assert isinstance(ctr, dict)
            assert "x" in ctr
            assert "y" in ctr
            assert "radius" in ctr


class TestGaugeDetectorResizeForDetect:
    """Test resize_for_detect utility."""

    def test_resize_small_image_unchanged(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        resized, scale = det.resize_for_detect(img)
        assert resized.shape[:2] == (100, 100)
        assert scale == 1.0

    def test_resize_large_image_downscales(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        img = np.zeros((2000, 2000, 3), dtype=np.uint8)
        resized, scale = det.resize_for_detect(img)
        # Should be resized so max dim <= 640
        h, w = resized.shape[:2]
        assert max(h, w) <= 640
        assert scale > 1.0  # Upscale factor


class TestGaugeDetectorFinalize:
    """Test finalize_result output cleanup."""

    def test_finalize_strips_debug_keys(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        cfg = make_default_config()
        result = {
            "value": 5.0,
            "angle": 90.0,
            "center": {"x": 100, "y": 100, "radius": 50},
            "error": None,
            "w": 640, "h": 480,
            "debug_preprocess": np.zeros((10, 10), dtype=np.uint8),
            "debug_binary": np.zeros((10, 10), dtype=np.uint8),
            "debug_preprocess_ann": np.zeros((10, 10, 3), dtype=np.uint8),
            "debug_binary_ann": np.zeros((10, 10, 3), dtype=np.uint8),
        }
        full_img = np.zeros((480, 640, 3), dtype=np.uint8)
        finalized = det.finalize_result(result, full_img, 1.0, cfg)
        for k in ["debug_preprocess", "debug_binary",
                   "debug_preprocess_ann", "debug_binary_ann"]:
            assert k not in finalized, f"Key {k} should be stripped"

    def test_finalize_keeps_essential_keys(self):
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector()
        cfg = make_default_config()
        result = {
            "value": 5.0,
            "angle": 90.0,
            "center": {"x": 100, "y": 100, "radius": 50},
            "error": None,
            "w": 640, "h": 480,
        }
        full_img = np.zeros((480, 640, 3), dtype=np.uint8)
        finalized = det.finalize_result(result, full_img, 1.0, cfg)
        assert "value" in finalized
        assert "angle" in finalized
        assert "center" in finalized


class TestDetectorEdgeCases:
    """Edge cases: None input, empty frames, extreme configs."""

    def test_detect_none_input_returns_error(self):
        """Passing None as frame returns error dict, not crash."""
        from gauge_reader.detector import GaugeDetector
        det = GaugeDetector(make_default_config())
        result = det.detect(None)
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] is not None

    def test_detect_zero_size_frame_handled(self):
        """Zero-size image returns error dict or empty result."""
        from gauge_reader.detector import GaugeDetector
        img = np.zeros((0, 0, 3), dtype=np.uint8)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        assert isinstance(result, dict)
        assert "error" in result or "value" in result

    def test_detect_config_extreme_values_no_crash(self):
        """Extreme config values (max blur, max threshold) should not crash."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config({
            "blur_kernel": 31,
            "threshold_block": 99,
            "circle_hough_param1": 999,
            "circle_hough_param2": 999,
            "min_confidence": 0.0,
        })
        det = GaugeDetector(cfg)
        result = det.detect(img)
        assert isinstance(result, dict)

    def test_detect_repeated_same_frame_stable_output(self):
        """Same frame detected 3 times with same instance should stabilize."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=60)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        results = [det.detect(img.copy()) for _ in range(3)]
        for r in results:
            assert r.get("error") is None
        angles = [r["angle"] for r in results if r.get("error") is None]
        if len(angles) >= 3:
            variance = np.var(angles)
            assert variance < 5.0, f"Angle variance {variance:.2f} too high: {angles}"
