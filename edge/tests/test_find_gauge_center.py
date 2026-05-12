import numpy as np
import cv2
from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy


def make_fake_gauge(cx=320, cy=240, radius=150):
    """Generate synthetic gauge image with dark circle on light background."""
    img = np.full((480, 640, 3), 220, dtype=np.uint8)
    cv2.circle(img, (cx, cy), radius, (60, 60, 60), 2)
    cv2.circle(img, (cx, cy), 4, (20, 20, 20), -1)
    return img


def test_detects_fake_gauge_circle():
    img = make_fake_gauge(320, 240, 150)
    result = find_gauge_center(img, use_clahe=False)
    assert result is not None
    cx, cy, radius = result
    assert abs(cx - 320) < 30, f"cx off: {cx}"
    assert abs(cy - 240) < 30, f"cy off: {cy}"
    assert 120 < radius < 180, f"radius off: {radius}"


def test_returns_none_on_blank_image():
    img = np.full((480, 640, 3), 128, dtype=np.uint8)
    result = find_gauge_center(img, use_clahe=False)
    assert result is None


def test_temporal_prior_beats_no_detection():
    img = np.full((480, 640, 3), 128, dtype=np.uint8)
    prev = (300, 200, 140)
    result = find_gauge_center(img, prev_center=prev, use_clahe=False)
    assert result is not None
    cx, cy, radius = result
    assert cx == 300 and cy == 200 and radius == 140


def test_legacy_works():
    img = make_fake_gauge(320, 240, 150)
    result = find_gauge_center_legacy(img)
    assert result is not None
    cx, cy, radius = result
    assert abs(cx - 320) < 30
    assert abs(cy - 240) < 30
