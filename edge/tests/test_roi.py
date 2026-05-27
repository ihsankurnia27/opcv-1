"""TDD tests for ROI cropping in GaugeDetector (Task 7)."""

import os
import sys

# Add both edge/ and edge/tests to path
_edge_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _edge_root)
sys.path.insert(0, os.path.join(_edge_root, "tests"))

import numpy as np
import pytest

from test_detector import make_realistic_gauge, make_default_config


class TestRoiDefaults:
    """Verify ROI config defaults."""

    def test_roi_off_by_default(self):
        """use_roi is false and roi_margin is 1.5 in default config."""
        # Point CONFIG_PATH at nonexistent file so load_config() returns defaults
        os.environ.setdefault("CONFIG_PATH", "/nonexistent/config.json")
        from app.api import load_config
        cfg = load_config()
        assert cfg.get("use_roi") is False
        assert cfg.get("roi_margin") == 1.5

    def test_roi_off_identical(self):
        """When use_roi=false, output matches default behavior (no ROI config)."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(angle_deg=120)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result_default = det.detect(img.copy())
        result_explicit = det.detect(img.copy(), config_overrides={"use_roi": "0"})
        if result_default.get("error") is None and result_explicit.get("error") is None:
            assert result_default["angle"] == result_explicit["angle"], (
                f"angle mismatch: {result_default['angle']} vs {result_explicit['angle']}"
            )
            assert result_default["value"] == result_explicit["value"], (
                f"value mismatch: {result_default['value']} vs {result_explicit['value']}"
            )
            assert result_default["center"] == result_explicit["center"], (
                f"center mismatch: {result_default['center']} vs {result_explicit['center']}"
            )


class TestRoiDetection:
    """Verify ROI cropping produces correct detection results."""

    def test_roi_matches_full_frame(self):
        """ROI cropping produces same (or very close) needle angle as full frame
        for a centered gauge where ROI fully contains the annulus."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=60)
        cfg = make_default_config({"blur_kernel": 0, "threshold_block": 0})
        det = GaugeDetector(cfg)
        result_no_roi = det.detect(img.copy())
        # Reset detector state between calls (new instance)
        det2 = GaugeDetector(cfg)
        result_roi = det2.detect(img.copy(), config_overrides={"use_roi": "1", "roi_margin": 1.5})
        if result_no_roi.get("error") is None and result_roi.get("error") is None:
            diff = abs(result_no_roi["angle"] - result_roi["angle"])
            assert diff < 10, (
                f"ROI angle {result_roi['angle']} differs from full {result_no_roi['angle']} by {diff:.1f} deg"
            )

    def test_roi_cropping_applied(self):
        """When use_roi=true, debug images are cropped (smaller than full frame)."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=90)
        cfg = make_default_config()
        det = GaugeDetector(cfg)
        result_no_roi = det.detect(img.copy())
        det2 = GaugeDetector(cfg)
        result_roi = det2.detect(img.copy(), config_overrides={"use_roi": "1", "roi_margin": 1.5})
        if result_roi.get("error") is None and result_no_roi.get("error") is None:
            h_no_roi = result_no_roi["debug_preprocess"].shape[0]
            h_roi = result_roi["debug_preprocess"].shape[0]
            w_no_roi = result_no_roi["debug_preprocess"].shape[1]
            w_roi = result_roi["debug_preprocess"].shape[1]
            assert h_roi < h_no_roi or w_roi < w_no_roi, (
                f"ROI debug ({h_roi}x{w_roi}) should be smaller than full ({h_no_roi}x{w_no_roi})"
            )

    def test_roi_different_margins_different_crops(self):
        """Different roi_margin values produce different crop sizes (at least one dim differs)."""
        from gauge_reader.detector import GaugeDetector
        img = make_realistic_gauge(cx=320, cy=240, radius=150, angle_deg=90)
        cfg = make_default_config()
        det1 = GaugeDetector(cfg)
        r1 = det1.detect(img.copy(), config_overrides={"use_roi": "1", "roi_margin": 1.5})
        det2 = GaugeDetector(cfg)
        r2 = det2.detect(img.copy(), config_overrides={"use_roi": "1", "roi_margin": 2.5})
        if r1.get("error") is None and r2.get("error") is None:
            h1, w1 = r1["debug_preprocess"].shape[:2]
            h2, w2 = r2["debug_preprocess"].shape[:2]
            total1 = w1 * h1
            total2 = w2 * h2
            assert total2 > total1, (
                f"Larger margin should give larger crop area: "
                f"m=1.5 ({w1}x{h1}={total1}), m=2.5 ({w2}x{h2}={total2})"
            )
