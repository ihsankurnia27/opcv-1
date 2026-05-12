"""Needle and gauge annotation drawing utilities."""

import cv2
import numpy as np


def draw_needle(image, cx, cy, radius, angle_deg, color=(0, 255, 0), thickness=2,
                inner_ratio=None, outer_ratio=None, min_angle=None, max_angle=None):
    """Draw detected needle, gauge circle, inner/outer sampling bands, and min/max ref lines."""
    h, w = image.shape[:2]
    r_end = int(radius * 0.85)
    rad = np.deg2rad(angle_deg)
    x2 = int(cx + r_end * np.cos(rad))
    y2 = int(cy + r_end * np.sin(rad))

    # Gauge outer circle
    cv2.circle(image, (cx, cy), radius, (255, 0, 0), 2)

    # Inner sampling circle
    if inner_ratio is not None:
        r_inner = int(radius * inner_ratio)
        cv2.circle(image, (cx, cy), r_inner, (255, 200, 0), 1)

    # Outer sampling circle
    if outer_ratio is not None:
        r_outer = int(radius * outer_ratio)
        cv2.circle(image, (cx, cy), r_outer, (255, 200, 0), 1)

    # Center dot
    cv2.circle(image, (cx, cy), 4, (0, 0, 255), -1)

    # Needle line
    cv2.line(image, (cx, cy), (x2, y2), color, thickness)

    # Min/Max reference lines
    ref_color = (255, 255, 0)
    for a in (min_angle, max_angle):
        if a is not None:
            arad = np.deg2rad(a)
            xr = int(cx + radius * 0.7 * np.cos(arad))
            yr = int(cy + radius * 0.7 * np.sin(arad))
            cv2.line(image, (cx, cy), (xr, yr), ref_color, 2)

    return image
