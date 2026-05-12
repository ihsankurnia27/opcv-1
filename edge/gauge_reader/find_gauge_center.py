"""Gauge center detection: Canny+HoughCircles → contour → temporal prior cascade."""

import cv2
import numpy as np


def _hough_circles(gray, image_w, image_h):
    """Canny edge + HoughCircles with gradient voting."""
    edges = cv2.Canny(gray, 50, 150)
    circles = cv2.HoughCircles(
        edges,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=image_h * 0.3,
        param1=100,
        param2=50,
        minRadius=int(image_w * 0.05),
        maxRadius=int(image_w * 0.45),
    )
    if circles is not None and len(circles) > 0:
        c = circles[0][0]
        return int(c[0]), int(c[1]), int(c[2])
    return None


def _contour_circularity(gray, image_w, image_h):
    """Find largest contour with circularity > 0.7, fit enclosing circle."""
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_score = 0
    min_area = np.pi * (image_w * 0.05) ** 2
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        perimeter = cv2.arcLength(cnt, True)
        if perimeter < 1:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity > 0.7 and circularity > best_score:
            best_score = circularity
            best = cnt
    if best is not None:
        (cx, cy), radius = cv2.minEnclosingCircle(best)
        return int(cx), int(cy), int(radius)
    return None


def find_gauge_center(image, prev_center=None, ema_alpha=0.3, use_clahe=True):
    """Locate gauge center & radius with three-strategy cascade.

    Strategies in order:
      A: Canny edge → HoughCircles with gradient voting
      B: Canny edge → largest circular contour → minEnclosingCircle
      C: Temporal prior (EMA-predicted center from previous frames)

    Args:
        image: BGR numpy array
        prev_center: optional (cx, cy, radius) from previous frame
        ema_alpha: not used directly here — caller applies EMA
        use_clahe: whether to apply CLAHE before detection

    Returns:
        (cx, cy, radius) or None
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    if use_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    # Strategy A: HoughCircles on Canny edges
    result = _hough_circles(gray, w, h)
    if result is not None:
        return result

    # Strategy B: Contour circularity
    result = _contour_circularity(gray, w, h)
    if result is not None:
        return result

    # Strategy C: Temporal prior
    if prev_center is not None:
        return (int(prev_center[0]), int(prev_center[1]), int(prev_center[2]))

    return None


def find_gauge_center_legacy(image):
    """Original SimpleBlobDetector → HoughCircles method. Kept for backward compat."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = True
    params.blobColor = 0
    params.filterByArea = True
    params.minArea = np.pi * (w * 0.05) ** 2
    params.maxArea = np.pi * (w * 0.45) ** 2
    params.filterByCircularity = True
    params.minCircularity = 0.3
    params.filterByConvexity = False
    params.filterByInertia = False

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)

    if keypoints:
        best = max(keypoints, key=lambda k: k.size)
        cx, cy = int(best.pt[0]), int(best.pt[1])
        radius = int(best.size / 2)
        if radius > 10:
            return cx, cy, radius

    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=h * 0.3,
        param1=80, param2=40, minRadius=int(w * 0.05), maxRadius=int(w * 0.45),
    )
    if circles is not None:
        c = circles[0][0]
        return int(c[0]), int(c[1]), int(c[2])

    return None
