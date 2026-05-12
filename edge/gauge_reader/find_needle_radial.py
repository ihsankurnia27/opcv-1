import numpy as np
import cv2

from gauge_reader.draw import draw_needle  # noqa: F401 — re-exported for legacy callers


def _preprocess(image, blur_kernel=5, threshold_block=0, threshold_c=5):
    """Grayscale + optional blur + optional adaptive threshold. Returns (gray, h, w)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur_kernel > 0:
        k = blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)
    if threshold_block > 0:
        b = threshold_block if threshold_block % 2 == 1 else threshold_block + 1
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, b, threshold_c)
    return gray


def _sample_radial(gray, cx, cy, radius, inner_ratio, outer_ratio):
    """Vectorized radial sampling. Returns intensities array (360, n_samples)."""
    h, w = gray.shape[:2]
    n_angles = 360
    r_inner = int(radius * inner_ratio)
    r_outer = int(radius * outer_ratio)
    n_samples = max(1, r_outer - r_inner + 1)
    thetas = np.deg2rad(np.arange(n_angles))
    cos_t = np.cos(thetas)
    sin_t = np.sin(thetas)
    ray = np.arange(n_samples)
    x_offsets = (cos_t[:, np.newaxis] * (r_inner + ray)).astype(int)
    y_offsets = (sin_t[:, np.newaxis] * (r_inner + ray)).astype(int)
    xs = np.clip(cx + x_offsets, 0, w - 1)
    ys = np.clip(cy + y_offsets, 0, h - 1)
    return gray[ys, xs]  # (360, n_samples)


def compute_variance_profile(image, cx, cy, radius,
                              inner_ratio=0.75, outer_ratio=0.95,
                              blur_kernel=5, threshold_block=0, threshold_c=5):
    """Compute radial variance profile (360 values) for a gauge.

    Returns (variances, smoothed) tuple:
      variances:  raw variance per angle
      smoothed:   5-element moving average (no boundary effects, 360 elements)
    Both are length-360 numpy arrays.
    Returns (None, None) if image is too uniform.
    """
    gray = _preprocess(image, blur_kernel, threshold_block, threshold_c)
    intensities = _sample_radial(gray, cx, cy, radius, inner_ratio, outer_ratio)
    variances = np.var(intensities.astype(np.float32), axis=1)
    if np.median(variances) < 10.0:
        return None, None
    kernel = np.ones(5) / 5
    triple = np.concatenate([variances, variances, variances])
    smoothed = np.convolve(triple, kernel, mode='same')[360:720]
    return variances, smoothed


def find_needle_angle(image, cx, cy, radius, inner_ratio=0.60, outer_ratio=0.80,
                      blur_kernel=5, threshold_block=0, threshold_c=5):
    """Detect needle angle via radial line pixel sampling.

    Samples grayscale intensity along radial lines from center to perimeter
    for 360 angles. The darkest line (minimum mean intensity) is the needle.

    inner_ratio, outer_ratio: sampling radii as fraction of gauge radius.
    inner_ratio=0.60 avoids center pin, outer_ratio=0.80 avoids tick marks.

    blur_kernel: Gaussian blur kernel size (0 = skip blur).
    threshold_block: adaptive threshold block size (0 = skip threshold).
    threshold_c: constant subtracted from local mean.

    Returns angle in degrees (0 = right, 90 = up, 180 = left, 270 = down).
    """
    gray = _preprocess(image, blur_kernel, threshold_block, threshold_c)
    h, w = gray.shape[:2]

    # sampling radius: inner_ratio to outer_ratio avoids tick marks + center pin
    r_inner = int(radius * inner_ratio)
    r_outer = int(radius * outer_ratio)
    n_angles = 360
    n_samples = r_outer - r_inner + 1

    # precompute unit vectors for each angle
    thetas = np.deg2rad(np.arange(n_angles))
    cos_t = np.cos(thetas)
    sin_t = np.sin(thetas)

    # for each angle, sample n_samples pixels along the radial line
    # optimised: for each radial point, compute its contribution to all angles
    # then stack into (n_angles, n_samples) array
    ray = np.arange(n_samples)
    x_offsets = (cos_t[:, np.newaxis] * (r_inner + ray)).astype(int)
    y_offsets = (sin_t[:, np.newaxis] * (r_inner + ray)).astype(int)

    xs = np.clip(cx + x_offsets, 0, w - 1)
    ys = np.clip(cy + y_offsets, 0, h - 1)

    intensities = gray[ys, xs]  # (360, n_samples)
    mean_intensities = np.mean(intensities, axis=1)

    best_idx = int(np.argmin(mean_intensities))

    # sub-degree refinement: fit parabola around best ±2°
    def parabola_fit(i):
        idx = np.arange(max(0, i - 2), min(n_angles, i + 3))
        if len(idx) < 3:
            return float(i)
        coeffs = np.polyfit(idx, mean_intensities[idx], 2)
        if coeffs[0] > 0:  # concave up -> minimum
            vertex = -coeffs[1] / (2 * coeffs[0])
            return float(np.clip(vertex, idx[0], idx[-1]))
        return float(i)

    refined = parabola_fit(best_idx)
    angle_deg = refined  # 0-360 degrees

    return angle_deg


def detect_scale_range(image, cx, cy, radius,
                       inner_ratio=0.75, outer_ratio=0.95,
                       min_gap_deg=25, variance_ratio=0.35,
                       blur_kernel=5, threshold_block=0, threshold_c=5):
    """Detect min/max gauge angles from tick-mark variance gap.

    Scale tick marks create high pixel variance along radial rays.
    The gap between scale ends has low variance. Finds the largest
    contiguous low-variance gap and maps edges to min/max angle.

    Returns (min_angle, max_angle) or None if no valid gap found.
    """
    gray = _preprocess(image, blur_kernel, threshold_block, threshold_c)
    intensities = _sample_radial(gray, cx, cy, radius, inner_ratio, outer_ratio)

    # Variance per angle: tick marks = high variance, gap = low variance
    variances = np.var(intensities.astype(np.float32), axis=1)

    # Guard: image too uniform (no scale marks)
    if np.median(variances) < 10.0:
        return None

    # Smooth variance to suppress needle dip
    kernel = np.ones(5) / 5
    triple = np.concatenate([variances, variances, variances])
    smoothed = np.convolve(triple, kernel, mode='same')[360:720]

    # Adaptive threshold: low variance = below fraction of median
    threshold = np.median(smoothed) * variance_ratio
    is_low = smoothed < threshold

    # Find contiguous low-variance gaps with wrap-around handling
    extended = np.concatenate([is_low, is_low])  # 720 elements
    gaps = []
    start = None
    for i in range(len(extended)):
        if extended[i] and start is None:
            start = i
        elif not extended[i] and start is not None:
            gaps.append((start, i))
            start = None
    if start is not None:
        gaps.append((start, len(extended)))

    # Filter and pick largest valid gap
    best_gap = None
    best_len = 0
    for gs, ge in gaps:
        length = ge - gs
        if min_gap_deg <= length <= 180 and length > best_len:
            best_gap = (gs, ge)
            best_len = length

    if best_gap is None:
        return None

    gs, ge = best_gap

    if ge > 360:
        # Gap wraps around 0°
        min_angle = round((ge - 360) % 360, 1)
        max_angle = round(gs % 360, 1)
    else:
        # Gap doesn't wrap — scale wraps the other way
        min_angle = round(ge % 360, 1)
        max_angle = round(gs % 360, 1)

    return (min_angle, max_angle)


def learn_gap_params(variance_profile, user_min_angle, user_max_angle):
    """Given a smoothed variance profile (360 values) and user-indicated min/max
    angles, compute optimal detection params for this gauge.

    Returns dict with:
      variance_ratio:  gap_variance_median / overall_median  (tuned threshold)
      min_gap_deg:     detected gap size in degrees
    """
    user_min_angle = int(round(user_min_angle % 360))
    user_max_angle = int(round(user_max_angle % 360))
    # Profile wrapped to [0, 360) for the gap region — find the region
    # between user_min and user_max that has low variance
    gap_angles = []
    i = user_min_angle
    while i != user_max_angle:
        gap_angles.append(i)
        i = (i + 1) % 360
    gap_median = np.median(variance_profile[gap_angles]) if gap_angles else 0
    overall_median = np.median(variance_profile)
    variance_ratio = max(0.05, min(0.5, gap_median / overall_median)) if overall_median > 0 else 0.1
    return {
        "variance_ratio": round(variance_ratio, 4),
    }
