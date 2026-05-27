"""Multi-strategy needle detection with confidence-weighted voting.

Strategies:
  A: Line   — Canny + HoughLinesP in annulus, geometric filter, primary
  B: Diff   — Background subtraction + PCA (requires reference image)
  C: Radial — Darkest ray method (legacy fallback, always available)
"""

import cv2
import numpy as np


def _needle_line_angle(gray, cx, cy, radius, inner_ratio, outer_ratio,
                       min_angle=None, max_angle=None):
    """Strategy A: Canny edge + HoughLinesP in annulus ROI.

    Returns (angle_degrees, confidence) or None.
    """
    h, w = gray.shape[:2]

    # Create annulus mask
    mask_outer = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask_outer, (cx, cy), int(radius * outer_ratio), 255, -1)
    mask_inner = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask_inner, (cx, cy), int(radius * inner_ratio), 255, -1)
    mask = cv2.bitwise_xor(mask_outer, mask_inner)

    masked = cv2.bitwise_and(gray, gray, mask=mask)
    edges = cv2.Canny(masked, 50, 150)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20,
                            minLineLength=int(radius * inner_ratio * 0.3),
                            maxLineGap=max(5, int(radius * 0.2)))
    if lines is None or len(lines) == 0:
        return None

    angles = []
    center_tol = radius * 0.15

    for line in lines:
        x1, y1, x2, y2 = line[0]
        dx, dy = x2 - x1, y2 - y1
        length = np.hypot(dx, dy)
        if length < radius * inner_ratio * 0.3:
            continue

        # Angle of line (OpenCV coords: 0=right, 90=down)
        angle = np.rad2deg(np.arctan2(dy, dx))
        if angle < 0:
            angle += 360

        # Angle range filter
        if min_angle is not None and max_angle is not None:
            if not _angle_in_range(angle, min_angle, max_angle, margin=10):
                continue

        # Center proximity: line extension must pass near center
        dist = _point_line_distance(cx, cy, x1, y1, x2, y2)
        if dist > center_tol:
            continue

        angles.append(angle)

    if not angles:
        return None

    median_angle = float(np.median(angles))
    # Confidence: more agreeing lines = higher confidence
    inliers = sum(1 for a in angles if abs(_angle_diff(a, median_angle)) < 10)
    confidence = min(1.0, inliers / max(1, len(angles)) * (len(angles) / 3.0))

    return median_angle, confidence


def _needle_radial_angle(gray, cx, cy, radius, inner_ratio, outer_ratio):
    """Strategy C: Darkest radial ray. Returns (angle_degrees, confidence) or None."""
    r_inner = int(radius * inner_ratio)
    r_outer = int(radius * outer_ratio)
    n_angles = 360
    n_samples = r_outer - r_inner + 1
    if n_samples < 1:
        return None

    thetas = np.deg2rad(np.arange(n_angles))
    cos_t = np.cos(thetas)
    sin_t = np.sin(thetas)
    ray = np.arange(n_samples)
    x_offsets = (cos_t[:, np.newaxis] * (r_inner + ray)).astype(int)
    y_offsets = (sin_t[:, np.newaxis] * (r_inner + ray)).astype(int)
    h, w = gray.shape[:2]
    xs = np.clip(cx + x_offsets, 0, w - 1)
    ys = np.clip(cy + y_offsets, 0, h - 1)
    intensities = gray[ys, xs]
    mean_intensities = np.mean(intensities, axis=1)
    best_idx = int(np.argmin(mean_intensities))

    # Sub-degree parabola fit
    n = len(mean_intensities)
    idx = np.arange(max(0, best_idx - 2), min(n, best_idx + 3))
    if len(idx) >= 3:
        coeffs = np.polyfit(idx, mean_intensities[idx], 2)
        if coeffs[0] > 0:
            vertex = -coeffs[1] / (2 * coeffs[0])
            refined = float(np.clip(vertex, idx[0], idx[-1]))
        else:
            refined = float(best_idx)
    else:
        refined = float(best_idx)

    # Confidence: how much darker the minimum is vs median
    med = np.median(mean_intensities)
    min_val = mean_intensities[best_idx]
    if med > 0:
        contrast = (med - min_val) / med
    else:
        contrast = 0
    confidence = min(1.0, contrast * 5)

    return refined, confidence


def _angle_in_range(angle, min_a, max_a, margin=5):
    """Check if angle is within [min_a-margin, max_a+margin] handling wrap."""
    a_min = (min_a - margin) % 360
    a_max = (max_a + margin) % 360
    if a_min <= a_max:
        return a_min <= angle <= a_max
    else:
        return angle >= a_min or angle <= a_max


def _angle_diff(a, b):
    """Shortest angular distance in degrees."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _point_line_distance(px, py, x1, y1, x2, y2):
    """Perpendicular distance from point to line segment."""
    return abs((x2 - x1) * (y1 - py) - (x1 - px) * (y2 - y1)) / np.hypot(x2 - x1, y2 - y1)


def _vote_angles(candidates):
    """Confidence-weighted cluster vote.

    candidates: list of (angle, confidence)
    Returns (best_angle, best_confidence)
    """
    if not candidates:
        return None, 0.0

    if len(candidates) == 1:
        return candidates[0]

    # Group by +/-5 degree agreement
    groups = []
    used = set()
    for i, (a1, c1) in enumerate(candidates):
        if i in used:
            continue
        group = [(a1, c1)]
        used.add(i)
        for j, (a2, c2) in enumerate(candidates):
            if j in used:
                continue
            if _angle_diff(a1, a2) <= 5:
                group.append((a2, c2))
                used.add(j)
        groups.append(group)

    # Pick largest group
    best_group = max(groups, key=len)

    if len(best_group) >= 2:
        # Weighted average (vector mean for wrap safety)
        angles = [a for a, _ in best_group]
        weights = [w for _, w in best_group]
        total_w = sum(weights)
        avg_sin = sum(np.sin(np.deg2rad(a)) * w for a, w in zip(angles, weights)) / total_w
        avg_cos = sum(np.cos(np.deg2rad(a)) * w for a, w in zip(angles, weights)) / total_w
        avg_angle = np.rad2deg(np.arctan2(avg_sin, avg_cos)) % 360
        confidence = max(w for _, w in best_group)
        return float(avg_angle), confidence
    else:
        angle, conf = best_group[0]
        # Penalty proportional to how much confidence is in this lone group vs all
        total_conf = sum(w for _, w in candidates)
        penalty = max(0.5, conf / max(0.01, total_conf))
        return angle, conf * penalty


def find_needle_angle(image, cx, cy, radius, inner_ratio=0.60, outer_ratio=0.80,
                      blur_kernel=0, threshold_block=0, threshold_c=0,
                      method="auto", background_ref=None,
                      min_angle=None, max_angle=None,
                      use_clahe=True):
    """Detect needle angle via multi-strategy voting.

    Args:
        image: BGR numpy array
        cx, cy, radius: gauge center
        method: "auto", "line", "radial", "diff"
        background_ref: optional grayscale reference for difference strategy
        min_angle, max_angle: calibration range for filtering

    Returns:
        dict: {"angle": float, "confidence": float, "method": str}
        or {"error": str} on failure
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if blur_kernel > 0:
        k = blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)

    if threshold_block > 0:
        b = threshold_block if threshold_block % 2 == 1 else threshold_block + 1
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, b, threshold_c)

    # candidates: list of (angle, confidence, method_name)
    candidates = []

    # Per-strategy confidence tracking
    line_confidence = None
    diff_confidence = None
    radial_confidence = None

    # Strategy A: Line detection
    if method in ("auto", "line"):
        result = _needle_line_angle(gray, cx, cy, radius, inner_ratio, outer_ratio,
                                    min_angle, max_angle)
        if result is not None:
            line_confidence = result[1]
            candidates.append((result[0], result[1], "line"))

    # Strategy B: Background difference
    if method in ("auto", "diff") and background_ref is not None:
        diff = cv2.absdiff(gray, background_ref)
        _, binary = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        ys, xs = np.where(binary > 0)
        if len(xs) > 20:
            # PCA on pixel coordinates
            pts = np.column_stack([xs - cx, ys - cy])
            cov = np.cov(pts.T)
            eigenvalues, eigenvectors = np.linalg.eig(cov)
            principal = eigenvectors[:, np.argmax(eigenvalues)]
            angle = np.rad2deg(np.arctan2(principal[1], principal[0])) % 360
            conf = min(1.0, len(xs) / 500.0)
            diff_confidence = conf
            candidates.append((float(angle), conf, "diff"))

    # Strategy C: Radial (darkest ray) — always available
    if method in ("auto", "radial"):
        result = _needle_radial_angle(gray, cx, cy, radius, inner_ratio, outer_ratio)
        if result is not None:
            radial_confidence = result[1]
            candidates.append((result[0], result[1], "radial"))

    if not candidates:
        return {"error": "could not find needle"}

    # Vote
    raw_candidates = [(a, c) for a, c, _ in candidates]
    angle, confidence = _vote_angles(raw_candidates)

    if angle is None:
        return {"error": "could not find needle"}

    # Determine which method the winning angle came from
    winning_method = candidates[0][2]
    best_dist = _angle_diff(angle, candidates[0][0])
    for a, c, m in candidates:
        d = _angle_diff(angle, a)
        if d < best_dist:
            best_dist = d
            winning_method = m

    # Strategy consensus: how many strategies agree within 5 deg
    if len(candidates) >= 2:
        angles_only = [a for a, _, _ in candidates]
        agree_pairs = 0
        for i in range(len(angles_only)):
            for j in range(i + 1, len(angles_only)):
                if _angle_diff(angles_only[i], angles_only[j]) <= 5:
                    agree_pairs += 1
        if agree_pairs >= 1:
            strategy_consensus = 1.0
        else:
            strategy_consensus = 0.5
    else:
        strategy_consensus = 0.0

    return {
        "angle": round(angle, 2),
        "confidence": round(confidence, 2),
        "method": str(winning_method),
        "line_confidence": line_confidence,
        "diff_confidence": diff_confidence,
        "radial_confidence": radial_confidence,
        "strategy_consensus": strategy_consensus,
    }
