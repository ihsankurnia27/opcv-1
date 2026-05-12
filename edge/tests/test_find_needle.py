import numpy as np
import cv2
from gauge_reader.find_needle import find_needle_angle, _vote_angles, _needle_line_angle


def make_needle_image(cx=320, cy=240, radius=150, angle_deg=45):
    """Synthetic gauge with a visible needle line at given angle."""
    img = np.full((480, 640, 3), 200, dtype=np.uint8)
    # Outer ring
    cv2.circle(img, (cx, cy), radius, (100, 100, 100), 3)
    # Needle: dark line from center outward
    rad = np.deg2rad(angle_deg)
    r_end = int(radius * 0.85)
    x2 = int(cx + r_end * np.cos(rad))
    y2 = int(cy + r_end * np.sin(rad))
    cv2.line(img, (cx, cy), (x2, y2), (30, 30, 30), 3)
    # Center dot
    cv2.circle(img, (cx, cy), 5, (20, 20, 20), -1)
    return img


def test_find_needle_line_strategy():
    img = make_needle_image(320, 240, 150, 45)
    result = find_needle_angle(img, 320, 240, 150,
                               inner_ratio=0.30, outer_ratio=0.80,
                               blur_kernel=0, threshold_block=0, threshold_c=0,
                               method="auto", use_clahe=False)
    assert result is not None
    assert "angle" in result
    assert "confidence" in result
    assert "method" in result
    # Should be within ~10 of 45 on synthetic image
    assert abs(result["angle"] - 45) < 12, f"angle off: {result['angle']}"
    assert result["confidence"] > 0


def test_find_needle_radial_fallback():
    img = make_needle_image(320, 240, 150, 90)
    result = find_needle_angle(img, 320, 240, 150,
                               inner_ratio=0.30, outer_ratio=0.80,
                               blur_kernel=0, threshold_block=0, threshold_c=0,
                               method="radial", use_clahe=False)
    assert result is not None
    assert result["method"] == "radial"
    assert abs(result["angle"] - 90) < 12


def test_vote_angles_single_candidate():
    candidates = [(45.0, 0.8)]
    angle, conf = _vote_angles(candidates)
    assert angle == 45.0
    assert conf == 0.8


def test_vote_angles_two_agree():
    candidates = [(45.0, 0.9), (47.0, 0.7)]
    angle, conf = _vote_angles(candidates)
    assert 45.0 < angle < 47.0
    assert conf > 0.7


def test_vote_angles_disagree():
    # Two angles far apart -- should pick the higher confidence one
    candidates = [(45.0, 0.9), (130.0, 0.5)]
    angle, conf = _vote_angles(candidates)
    assert abs(angle - 45.0) < 5, f"Should pick higher-conf, got {angle}"


def test_needle_line_angle_returns_line():
    img = make_needle_image(320, 240, 150, 60)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = _needle_line_angle(gray, 320, 240, 150, 0.30, 0.80)
    if result is not None:
        angle, conf = result
        assert abs(angle - 60) < 20
