import numpy as np
import cv2


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
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Gaussian blur
    if blur_kernel > 0:
        k = blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)

    # Adaptive threshold — converts to binary (255=white, 0=black)
    if threshold_block > 0:
        b = threshold_block if threshold_block % 2 == 1 else threshold_block + 1
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, b, threshold_c)

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


def draw_needle(image, cx, cy, radius, angle_deg, color=(0, 255, 0), thickness=2):
    """Draw detected needle line on image for visual verification."""
    h, w = image.shape[:2]
    r_end = int(radius * 0.85)
    rad = np.deg2rad(angle_deg)
    x2 = int(cx + r_end * np.cos(rad))
    y2 = int(cy + r_end * np.sin(rad))
    cv2.line(image, (cx, cy), (x2, y2), color, thickness)
    cv2.circle(image, (cx, cy), 4, (0, 0, 255), -1)
    cv2.circle(image, (cx, cy), radius, (255, 0, 0), 2)
    return image
