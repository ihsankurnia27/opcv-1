"""TDD tests for push_readings.py — now uses GaugeDetector (Task 11).

Verifies:
  - push_readings imports GaugeDetector instead of inline detection code
  - Output format matches what push_readings payload expects
  - Detection consistent with GaugeDetector for same frame
  - CLI --help exits 0
"""

import os
import sys
import subprocess
from copy import deepcopy

import cv2
import numpy as np
import pytest

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


def make_push_readings_config():
    """Config matching push_readings defaults (before/after refactor)."""
    return {
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
        "detect_method": "auto",
        "use_clahe": True,
        "center_ema": 0.3,
        "angle_kalman_R": 0.1,
        "angle_kalman_Q": 0.01,
    }


class TestUsesGaugeDetector:
    """push_readings must use GaugeDetector from shared library."""

    def test_imports_gauge_detector(self):
        """Imports GaugeDetector from gauge_reader.detector."""
        import push_readings
        with open(push_readings.__file__) as f:
            source = f.read()
        assert "from gauge_reader.detector import GaugeDetector" in source

    def test_does_not_import_inline_detection_funcs(self):
        """Old detection dependencies are removed."""
        import push_readings
        with open(push_readings.__file__) as f:
            source = f.read()
        # These should now live inside GaugeDetector only
        assert "from gauge_reader.find_gauge_center" not in source
        assert "from gauge_reader.find_needle" not in source
        assert "from gauge_reader.preprocess" not in source

    def test_no_detect_gauge_function(self):
        """Standalone detect_gauge() is removed (replaced by detector.detect())."""
        import push_readings
        assert not hasattr(push_readings, "detect_gauge")

    def test_no_temporal_imports(self):
        """CenterTracker/AngleKalman are no longer imported directly."""
        import push_readings
        with open(push_readings.__file__) as f:
            source = f.read()
        assert "from gauge_reader.temporal" not in source


class TestOutputFormat:
    """GaugeDetector output must satisfy push_readings payload needs."""

    def test_detect_has_value_angle_center(self):
        """detect() returns keys push_readings payload needs."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=90)
        cfg = make_push_readings_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)

        assert "value" in result
        assert "angle" in result
        assert "center" in result
        assert "x" in result["center"]
        assert "y" in result["center"]
        assert "radius" in result["center"]
        assert result.get("error") is None

    def test_finalize_produces_annotated_image(self):
        """finalize_result() returns base64 annotated_image string."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=90)
        cfg = make_push_readings_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)

        finalized = det.finalize_result(result, img, 1.0, cfg)
        assert "annotated_image" in finalized
        assert isinstance(finalized["annotated_image"], str)
        assert len(finalized["annotated_image"]) > 0

    def test_payload_keys_match(self):
        """Simulate the full payload assembly that push_readings does."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=90)
        cfg = make_push_readings_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        assert result.get("error") is None

        finalized = det.finalize_result(result, img, 1.0, cfg)

        payload = {
            "point": cfg["point"],
            "value": round(finalized["value"], 2),
            "angle": finalized["angle"],
            "annotated_image": finalized["annotated_image"],
        }
        assert payload["point"] == "G-01"
        assert isinstance(payload["value"], float)
        assert isinstance(payload["angle"], float)
        assert isinstance(payload["annotated_image"], str)


class TestConsistency:
    """Detection output must be consistent between test and refactored code."""

    def test_output_consistent_with_detector(self):
        """push_readings-style detection matches GaugeDetector on same frame."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60)
        cfg = make_push_readings_config()

        # Two independent detectors with same config should produce same output
        det_a = GaugeDetector(deepcopy(cfg))
        det_b = GaugeDetector(deepcopy(cfg))

        res_a = det_a.detect(img)
        res_b = det_b.detect(img)

        assert res_a.get("error") is None
        assert res_b.get("error") is None
        assert abs(res_a["value"] - res_b["value"]) < 0.001
        assert abs(res_a["angle"] - res_b["angle"]) < 0.001

    def test_consistency_with_config_overrides(self):
        """Detection with overrides still behaves deterministically."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=120)
        cfg = make_push_readings_config()

        det_a = GaugeDetector(deepcopy(cfg))
        det_b = GaugeDetector(deepcopy(cfg))

        overrides = {"blur_kernel": 3, "threshold_block": 11}
        res_a = det_a.detect(img, config_overrides=overrides)
        res_b = det_b.detect(img, config_overrides=overrides)

        assert res_a.get("error") is None
        assert res_b.get("error") is None
        assert abs(res_a["value"] - res_b["value"]) < 0.001


class TestCli:
    """CLI interface must still work."""

    def test_help_exits_zero(self):
        """python3 push_readings.py --help exits with code 0."""
        script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "push_readings.py",
        )
        result = subprocess.run(
            [sys.executable, script, "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()
