import cv2
import numpy as np


def find_gauge_center(image):
    """Locate gauge center & radius.

    Tries SimpleBlobDetector on dark regions first.
    Falls back to HoughCircles if blob detection fails.

    Returns (cx, cy, radius) or None.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    # --- Blob detector approach ---
    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = True
    params.blobColor = 0  # dark blobs
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
        # pick largest dark blob
        best = max(keypoints, key=lambda k: k.size)
        cx, cy = int(best.pt[0]), int(best.pt[1])
        radius = int(best.size / 2)
        if radius > 10:
            return cx, cy, radius

    # --- Fallback: HoughCircles ---
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=h * 0.3,
        param1=80,
        param2=40,
        minRadius=int(w * 0.05),
        maxRadius=int(w * 0.45),
    )
    if circles is not None:
        c = circles[0][0]
        cx, cy, radius = int(c[0]), int(c[1]), int(c[2])
        return cx, cy, radius

    return None
