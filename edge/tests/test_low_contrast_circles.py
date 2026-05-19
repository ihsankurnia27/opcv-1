import numpy as np
import cv2
import pytest
from gauge_reader.find_gauge_center import find_gauge_center

def make_low_contrast_gauge(cx=320, cy=240, radius=150, fg=190, bg=210):
    """Generate synthetic gauge image with very faint rim."""
    img = np.full((480, 640, 3), bg, dtype=np.uint8)
    # Draw a faint circle
    cv2.circle(img, (cx, cy), radius, (fg, fg, fg), 2)
    # Optional: draw center point
    cv2.circle(img, (cx, cy), 2, (fg, fg, fg), -1)
    return img

def make_broken_rim_gauge(cx=320, cy=240, radius=150, fg=60, bg=220):
    """Generate synthetic gauge image with a dashed/broken rim."""
    img = np.full((480, 640, 3), bg, dtype=np.uint8)
    # Draw dashed circle with smaller gaps (2 degrees instead of 5)
    for angle in range(0, 360, 5):
        start_angle = angle
        end_angle = angle + 3
        cv2.ellipse(img, (cx, cy), (radius, radius), 0, start_angle, end_angle, (fg, fg, fg), 2)
    return img

def test_default_fails_low_contrast():
    """Verify that default detection (Canny/Hough) fails on very low contrast."""
    # 205 vs 210 is extremely low contrast (5 units)
    img = make_low_contrast_gauge(fg=205, bg=210)
    result = find_gauge_center(img, use_clahe=False)
    assert result is None, f"Default detection should fail on extremely low contrast (found {result})"

def test_adaptive_thresh_success_low_contrast():
    """Verify that enabling circle_adaptive_thresh succeeds on low contrast."""
    # 200 vs 210 (contrast 10) should be enough for adaptive but fail Canny
    img = make_low_contrast_gauge(fg=200, bg=210)

    # Verify it fails without adaptive first just to be sure
    assert find_gauge_center(img, use_clahe=False) is None

    # Use adaptive thresholding
    result = find_gauge_center(img, use_clahe=False, circle_adaptive_thresh=True)
    assert result is not None, "Adaptive threshold should detect the low-contrast circle"
    cx, cy, r = result
    assert abs(cx - 320) < 15
    assert abs(cy - 240) < 15

def test_dilation_helps_broken_rim():
    """Verify that circle_dilate helps detection on broken rims."""
    img = make_broken_rim_gauge(fg=40, bg=220) # Higher contrast for broken rim to focus on connectivity

    # Force Strategy B by making Strategy A fail
    # Use a high param2 for Hough
    # Without dilation, it should fail (contours are fragments, not a circle)
    result_no_dilate = find_gauge_center(img, use_clahe=False, circle_hough_param2=200, circle_dilate=0)
    assert result_no_dilate is None, "Broken rim should fail without dilation"

    # Now try with dilation + adaptive threshold + lower circularity
    # 5 pixels should bridge the 5-degree gaps
    result_dilate = find_gauge_center(
        img,
        use_clahe=False,
        circle_hough_param2=200,
        circle_dilate=5,
        circle_adaptive_thresh=True,
        circle_min_circularity=0.5
    )

    assert result_dilate is not None, "Dilation + Adaptive + Lower circularity should help connect the broken rim"
    cx, cy, r = result_dilate
    assert abs(cx - 320) < 20
    assert abs(cy - 240) < 20
