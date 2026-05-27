"""TDD tests for confidence-based rejection in detection output (Task 6).

Verifies:
- Detection result includes "confidence": float (0-1)
- Config includes min_confidence (default 0.0)
- Rejection logic when confidence < min_confidence
- No rejection when min_confidence is 0
- Confidence consistency across repeated detections
"""

import os
import sys

_edge_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _edge_root)
sys.path.insert(0, os.path.join(_edge_root, "tests"))

import cv2
import numpy as np
import pytest

from test_detector import make_realistic_gauge, make_default_config


class TestConfidenceField:
    """Detection result includes confidence field."""

    def test_confidence_in_result(self):
        """Detection result has 'confidence' key."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            assert "confidence" in result, "Missing 'confidence' in result"

    def test_confidence_is_float(self):
        """Confidence value is a float."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            assert isinstance(result["confidence"], float)

    def test_confidence_in_range(self):
        """Confidence is between 0 and 1 (inclusive)."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            c = result["confidence"]
            assert 0.0 <= c <= 1.0, f"Confidence {c} out of range [0, 1]"


class TestRejection:
    """Rejection logic when confidence < min_confidence."""

    def test_rejected_when_below_min_confidence(self):
        """When confidence < min_confidence, rejected=true."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config({"min_confidence": 0.99})
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            assert result.get("rejected") is True, (
                f"Expected rejected=True for min_confidence=0.99, "
                f"got confidence={result['confidence']}"
            )

    def test_not_rejected_when_min_confidence_zero(self):
        """min_confidence=0.0 means never reject."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config({"min_confidence": 0.0})
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            assert result.get("rejected") is False, (
                "Expected rejected=False when min_confidence=0.0"
            )

    def test_not_rejected_when_above_threshold(self):
        """When confidence >= min_confidence, rejected=false."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config({"min_confidence": 0.0})
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            conf = result["confidence"]
            # Use result's confidence as the threshold — should not reject itself
            cfg2 = make_default_config({"min_confidence": conf})
            det2 = GaugeDetector(cfg2)
            result2 = det2.detect(img)
            if result2.get("error") is None:
                assert result2.get("rejected") is False, (
                    f"Expected rejected=False when min_confidence={conf} "
                    f"equals confidence={result2['confidence']}"
                )

    def test_rejected_has_value(self):
        """Rejected detection still includes value (not an error)."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=90)
        cfg = make_default_config({"min_confidence": 0.99})
        det = GaugeDetector(cfg)
        result = det.detect(img)
        if result.get("error") is None:
            assert result.get("rejected") is True
            assert "value" in result, "Rejected result missing 'value'"
            assert result["value"] is not None


class TestMinConfidenceConfig:
    """min_confidence config key integration."""

    def test_min_confidence_default_in_load_config(self):
        """load_config() returns min_confidence=0.0 as default."""
        os.environ.setdefault("CONFIG_PATH", "/nonexistent/config.json")
        from app.api import load_config
        cfg = load_config()
        assert "min_confidence" in cfg, "min_confidence missing from defaults"
        assert cfg["min_confidence"] == 0.0

    def test_min_confidence_in_allowed_detect_keys(self):
        """min_confidence is in ALLOWED_DETECT_KEYS."""
        from app.api import ALLOWED_DETECT_KEYS
        assert "min_confidence" in ALLOWED_DETECT_KEYS


class TestConfidenceConsistency:
    """Confidence consistency across repeated detections."""

    def test_confidence_consistent(self):
        """Same frame produces same confidence value."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=60)
        cfg = make_default_config()
        det1 = GaugeDetector(cfg)
        det2 = GaugeDetector(cfg)
        r1 = det1.detect(img.copy())
        r2 = det2.detect(img.copy())
        if r1.get("error") is None and r2.get("error") is None:
            assert r1["confidence"] == r2["confidence"], (
                f"Confidence mismatch: {r1['confidence']} vs {r2['confidence']}"
            )

    def test_min_confidence_accepted_by_set_stream_detect_config(self):
        """min_confidence can be sent via stream-detect-config."""
        from app.api import ALLOWED_DETECT_KEYS
        assert "min_confidence" in ALLOWED_DETECT_KEYS


class TestConfidenceLowContrast:
    """Confidence varies with image quality."""

    def test_confidence_low_contrast_image(self):
        """Low contrast synthetic gauge produces lower confidence than high contrast."""
        from gauge_reader.detector import GaugeDetector

        img_high = make_realistic_gauge(angle_deg=60)

        # Very low contrast version — faint gray needle on similar gray bg
        img_low = np.full((480, 640, 3), 150, dtype=np.uint8)
        cv2.circle(img_low, (320, 240), 165, (145, 145, 145), 2)
        cv2.circle(img_low, (320, 240), 150, (148, 148, 148), 3)
        rad = np.deg2rad(60)
        x2 = int(320 + 125 * np.cos(rad))
        y2 = int(240 + 125 * np.sin(rad))
        cv2.line(img_low, (320, 240), (x2, y2), (135, 135, 135), 3)
        cv2.circle(img_low, (320, 240), 6, (140, 140, 140), -1)

        cfg = make_default_config()
        det_high = GaugeDetector(cfg)
        det_low = GaugeDetector(cfg)

        r_high = det_high.detect(img_high)
        r_low = det_low.detect(img_low)

        if r_high.get("error") is None and r_low.get("error") is None:
            assert r_low["confidence"] <= r_high["confidence"], (
                f"Low contrast confidence {r_low['confidence']:.3f} should be <= "
                f"high contrast {r_high['confidence']:.3f}"
            )
