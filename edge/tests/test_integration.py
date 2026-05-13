import numpy as np
import cv2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
