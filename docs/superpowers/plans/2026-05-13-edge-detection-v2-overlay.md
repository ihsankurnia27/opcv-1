# Edge Detection Pipeline v2 + Universal Overlay — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fragile dark-ray needle detection with multi-strategy voting pipeline + CLAHE preprocessing + temporal filtering, and add real-time canvas overlay annotations to client cam live feed.

**Architecture:** Four new gauge_reader modules (preprocess.py, find_needle.py, temporal.py, draw.py) + rewrite find_gauge_center.py with Canny+Hough+contour cascade. api.py wires new pipeline behind `detect_method` config flag with full backward compatibility. Frontend adds JS canvas overlay loop polling `/detect` for client cam annotation.

**Tech Stack:** Python 3.12, OpenCV 4.10, NumPy, FastAPI — all already in requirements.txt. Zero new dependencies.

---

### Task 1: Extract draw_needle to own module

**Files:**
- Create: `edge/gauge_reader/draw.py`
- Modify: `edge/gauge_reader/find_needle_radial.py`

Extract `draw_needle()` from `find_needle_radial.py` into its own module so it's importable without pulling the legacy radial detection path. Legacy module re-imports from draw.py for backward compat.

- [ ] **Step 1: Create `edge/gauge_reader/draw.py`**

```python
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
```

- [ ] **Step 2: Update `edge/gauge_reader/find_needle_radial.py` — replace inline draw_needle with import**

In `find_needle_radial.py`, delete the entire `draw_needle()` function (lines 215-252) and add at top:

```python
from gauge_reader.draw import draw_needle  # noqa: F401 — re-exported for legacy callers
```

- [ ] **Step 3: Verify imports work**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "from gauge_reader.draw import draw_needle; from gauge_reader.find_needle_radial import draw_needle; print('OK')"
```

Expected: `OK` (no errors)

- [ ] **Step 4: Commit**

```bash
git add edge/gauge_reader/draw.py edge/gauge_reader/find_needle_radial.py
git commit -m "refactor: extract draw_needle to gauge_reader/draw.py"
```

---

### Task 2: Create preprocessing module

**Files:**
- Create: `edge/gauge_reader/preprocess.py`

CLAHE-based lighting normalization, bilateral denoising, optional background subtraction. All functions operate on BGR input.

- [ ] **Step 1: Write failing test**

Create `edge/tests/test_preprocess.py`:

```python
import numpy as np
import cv2
from gauge_reader.preprocess import to_lab_l_channel, apply_clahe, bilateral_denoise


def test_to_lab_l_channel_shape():
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = to_lab_l_channel(img)
    assert result.shape == (480, 640)
    assert result.dtype == np.uint8


def test_apply_clahe_output_range():
    gray = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
    result = apply_clahe(gray)
    assert result.shape == gray.shape
    assert result.dtype == np.uint8
    assert result.min() >= 0
    assert result.max() <= 255


def test_apply_clahe_enhances_contrast():
    # Dark image with subtle gradient — CLAHE should increase std dev
    gray = (np.random.randn(200, 200) * 10 + 50).clip(0, 255).astype(np.uint8)
    result = apply_clahe(gray, clip=2.0, tile=8)
    assert result.std() >= gray.std() * 0.9  # at minimum doesn't destroy contrast


def test_bilateral_denoise_preserves_edges():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[80:120, 80:120] = 255  # sharp white square
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = bilateral_denoise(img)
    edge_original = cv2.Canny(gray, 50, 150).sum()
    edge_result = cv2.Canny(cv2.cvtColor(result, cv2.COLOR_BGR2GRAY), 50, 150).sum()
    # Bilateral should preserve edge structure (edges don't vanish)
    assert edge_result >= edge_original * 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_preprocess.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Create `edge/gauge_reader/preprocess.py`**

```python
"""Preprocessing: CLAHE lighting normalization, bilateral denoising, background subtraction."""

import cv2
import numpy as np


def to_lab_l_channel(img):
    """Convert BGR to LAB, return L channel (perceptual luminance)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    return lab[:, :, 0]


def apply_clahe(gray, clip=2.0, tile=8):
    """Apply CLAHE to grayscale image for lighting normalization."""
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    return clahe.apply(gray)


def bilateral_denoise(img):
    """Edge-preserving bilateral filter on BGR image."""
    return cv2.bilateralFilter(img, 5, 75, 75)


def build_background_model(frames):
    """Median of N frames as background reference. Input: list of grayscale ndarrays."""
    if not frames:
        return None
    stack = np.stack(frames, axis=0)
    return np.median(stack, axis=0).astype(np.uint8)


def subtract_background(gray, ref):
    """Absolute difference with Otsu binarization. Returns binary mask."""
    if ref is None:
        return None
    diff = cv2.absdiff(gray, ref)
    _, binary = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def preprocess(img, clahe=True, denoise=True):
    """Full preprocessing pipeline: BGR → LAB L → CLAHE → back to BGR via merge + bilateral.

    Returns BGR image ready for center/needle detection.
    """
    l_channel = to_lab_l_channel(img)
    if clahe:
        l_channel = apply_clahe(l_channel)
    # Merge back to BGR for downstream color-agnostic operations
    result = cv2.cvtColor(l_channel, cv2.COLOR_GRAY2BGR)
    if denoise:
        result = bilateral_denoise(result)
    return result
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_preprocess.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add edge/gauge_reader/preprocess.py edge/tests/test_preprocess.py
git commit -m "feat: add preprocessing module with CLAHE, bilateral, background subtract"
```

---

### Task 3: Create temporal filtering module

**Files:**
- Create: `edge/gauge_reader/temporal.py`

EMA center tracker + 1D Kalman angle filter. No external dependencies beyond NumPy.

- [ ] **Step 1: Write failing test**

Create `edge/tests/test_temporal.py`:

```python
import numpy as np
from gauge_reader.temporal import CenterTracker, AngleKalman


def test_center_tracker_ema_converges():
    tracker = CenterTracker(ema_alpha=0.3)
    # Feed same center 10 times
    for _ in range(10):
        tracker.update(100, 200, 150)
    cx, cy, r = tracker.get()
    assert abs(cx - 100) < 2, f"EMA should converge near 100, got {cx}"
    assert abs(cy - 200) < 2
    assert abs(r - 150) < 2


def test_center_tracker_rejects_none_when_uninitialized():
    tracker = CenterTracker(ema_alpha=0.3)
    cx, cy, r = tracker.get()
    assert cx == 0 and cy == 0 and r == 0


def test_angle_kalman_smooths_jumps():
    kf = AngleKalman(R=0.1, Q=0.01)
    # Initialize
    init = kf.update(45.0)
    assert init == 45.0
    # Small change tracked
    a1 = kf.update(46.0)
    assert 45.0 < a1 < 46.0, f"Kalman should smooth step, got {a1}"


def test_angle_kalman_converges_to_constant():
    kf = AngleKalman(R=0.1, Q=0.01)
    kf.update(90.0)
    for _ in range(20):
        result = kf.update(90.0)
    assert abs(result - 90.0) < 0.5, f"Should converge to constant 90, got {result}"


def test_angle_kalman_initial_measurement_sets_state():
    kf = AngleKalman(R=0.1, Q=0.01)
    result = kf.update(270.0)
    assert result == 270.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_temporal.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Create `edge/gauge_reader/temporal.py`**

```python
"""Temporal filtering: center position EMA + 1D Kalman angle filter."""

import numpy as np


class CenterTracker:
    """EMA smoothing on gauge center (cx, cy, radius) across frames."""

    def __init__(self, ema_alpha=0.3):
        self.alpha = ema_alpha
        self._cx = 0.0
        self._cy = 0.0
        self._radius = 0.0
        self._initialized = False

    def update(self, cx, cy, radius):
        if not self._initialized:
            self._cx = float(cx)
            self._cy = float(cy)
            self._radius = float(radius)
            self._initialized = True
        else:
            self._cx = self.alpha * cx + (1 - self.alpha) * self._cx
            self._cy = self.alpha * cy + (1 - self.alpha) * self._cy
            self._radius = self.alpha * radius + (1 - self.alpha) * self._radius

    def get(self):
        return self._cx, self._cy, self._radius

    @property
    def initialized(self):
        return self._initialized

    def reset(self):
        self.__init__(self.alpha)


class AngleKalman:
    """1D Kalman filter (constant position model) for needle angle smoothing.

    State: [angle]
    Predict: x = x (needle assumed stationary between frames)
    Update:  x = x + K * (measurement - x)
    """

    def __init__(self, R=0.1, Q=0.01):
        self.R = R  # measurement noise
        self.Q = Q  # process noise
        self._x = None  # state estimate
        self._P = None  # error covariance

    def update(self, measurement):
        measurement = float(measurement)
        if self._x is None:
            self._x = measurement
            self._P = 1.0
            return measurement

        # Predict
        x_pred = self._x
        P_pred = self._P + self.Q

        # Update
        K = P_pred / (P_pred + self.R)
        self._x = x_pred + K * (measurement - x_pred)
        self._P = (1 - K) * P_pred

        return float(self._x)

    def reset(self):
        self._x = None
        self._P = None
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_temporal.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add edge/gauge_reader/temporal.py edge/tests/test_temporal.py
git commit -m "feat: add temporal filtering module with CenterTracker and AngleKalman"
```

---

### Task 4: Rewrite center detection with cascade + temporal prior

**Files:**
- Modify: `edge/gauge_reader/find_gauge_center.py`

Three-strategy cascade: Canny+HoughCircles → contour circularity → temporal prior. Old function renamed to `_find_gauge_center_legacy` for backward compat. New function is the default.

- [ ] **Step 1: Write failing test**

Create `edge/tests/test_find_gauge_center.py`:

```python
import numpy as np
import cv2
from gauge_reader.find_gauge_center import find_gauge_center


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
    cx, cy, radius, conf = result
    assert abs(cx - 320) < 30, f"cx off: {cx}"
    assert abs(cy - 240) < 30, f"cy off: {cy}"
    assert 120 < radius < 180, f"radius off: {radius}"
    assert conf > 0.5


def test_returns_none_on_blank_image():
    img = np.full((480, 640, 3), 128, dtype=np.uint8)
    result = find_gauge_center(img, use_clahe=False)
    assert result is None


def test_temporal_prior_beats_no_detection():
    img = np.full((480, 640, 3), 128, dtype=np.uint8)
    prev = (300, 200, 140)
    result = find_gauge_center(img, prev_center=prev, use_clahe=False)
    assert result is not None
    cx, cy, radius, conf = result
    assert cx == 300 and cy == 200 and radius == 140
    assert conf < 0.5, "temporal prior should have low confidence"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_find_gauge_center.py -v
```

Expected: FAIL — new function signature not found

- [ ] **Step 3: Rewrite `edge/gauge_reader/find_gauge_center.py`**

```python
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
        return int(c[0]), int(c[1]), int(c[2]), 0.9
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
        return int(cx), int(cy), int(radius), 0.7
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
        (cx, cy, radius, confidence) or None
        confidence: 0.0-1.0 (1.0 = Hough found perfect circle)
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
        return (int(prev_center[0]), int(prev_center[1]), int(prev_center[2]), 0.3)

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
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_find_gauge_center.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add edge/gauge_reader/find_gauge_center.py edge/tests/test_find_gauge_center.py
git commit -m "refactor: rewrite center detection with Canny+Hough+contour cascade + temporal prior"
```

---

### Task 5: Create multi-strategy needle detection module

**Files:**
- Create: `edge/gauge_reader/find_needle.py`

Three-strategy voting: line detection (primary), background difference, radial dark ray. Confidence-weighted cluster vote.

- [ ] **Step 1: Write tests**

Create `edge/tests/test_find_needle.py`:

```python
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
    # Should be within ~8° of 45 on synthetic image
    assert abs(result["angle"] - 45) < 10, f"angle off: {result['angle']}"
    assert result["confidence"] > 0


def test_find_needle_radial_fallback():
    img = make_needle_image(320, 240, 150, 90)
    result = find_needle_angle(img, 320, 240, 150,
                               inner_ratio=0.30, outer_ratio=0.80,
                               blur_kernel=0, threshold_block=0, threshold_c=0,
                               method="radial", use_clahe=False)
    assert result is not None
    assert result["method"] == "radial"
    assert abs(result["angle"] - 90) < 10


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
    # Two angles far apart — should pick the higher confidence one
    candidates = [(45.0, 0.9), (130.0, 0.5)]
    angle, conf = _vote_angles(candidates)
    assert abs(angle - 45.0) < 5, f"Should pick higher-conf, got {angle}"


def test_needle_line_angle_returns_line():
    img = make_needle_image(320, 240, 150, 60)
    result = _needle_line_angle(img, 320, 240, 150, 0.30, 0.80)
    if result is not None:
        angle, conf = result
        assert abs(angle - 60) < 15


def test_find_needle_returns_none_for_blank():
    img = np.full((480, 640, 3), 128, dtype=np.uint8)
    result = find_needle_angle(img, 320, 240, 150,
                               inner_ratio=0.30, outer_ratio=0.80,
                               blur_kernel=0, threshold_block=0, threshold_c=0,
                               method="auto", use_clahe=False)
    # May return error dict or None
    if result is not None:
        assert "error" in result or result.get("confidence", 0) < 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ihsan/opov-1/edge && python3 -m pytest tests/test_find_needle.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Create `edge/gauge_reader/find_needle.py`**

```python
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
    # Create annulus mask
    h, w = gray.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (cx, cy), int(radius * outer_ratio), 255, -1)
    cv2.circle(mask, (cx, cy), int(radius * inner_ratio), 255, -1)
    mask = cv2.bitwise_xor(
        cv2.circle(np.zeros((h, w), dtype=np.uint8), (cx, cy), int(radius * outer_ratio), 255, -1),
        cv2.circle(np.zeros((h, w), dtype=np.uint8), (cx, cy), int(radius * inner_ratio), 255, -1),
    )

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

        # Angle of line (openCV coords: 0=right, 90=down)
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

    # Group by ±5° agreement
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
        # Weighted average
        total_w = sum(w for _, w in best_group)
        angles = [a for a, _ in best_group]
        weights = [w for _, w in best_group]
        # Handle wrap-around for averaging
        avg_sin = sum(np.sin(np.deg2rad(a)) * w for a, w in zip(angles, weights)) / total_w
        avg_cos = sum(np.cos(np.deg2rad(a)) * w for a, w in zip(angles, weights)) / total_w
        avg_angle = np.rad2deg(np.arctan2(avg_sin, avg_cos)) % 360
        confidence = max(w for _, w in best_group)
        return float(avg_angle), confidence
    else:
        angle, conf = best_group[0]
        return angle, conf * 0.5


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

    candidates = []

    # Strategy A: Line detection
    if method in ("auto", "line"):
        result = _needle_line_angle(gray, cx, cy, radius, inner_ratio, outer_ratio,
                                    min_angle, max_angle)
        if result is not None:
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
            candidates.append((float(angle), conf, "diff"))

    # Strategy C: Radial (darkest ray) — always available
    if method in ("auto", "radial"):
        result = _needle_radial_angle(gray, cx, cy, radius, inner_ratio, outer_ratio)
        if result is not None:
            candidates.append((result[0], result[1] * 0.6, "radial"))

    if not candidates:
        return {"error": "could not find needle"}

    # Vote
    raw_candidates = [(a, c) for a, c, _ in candidates]
    angle, confidence = _vote_angles(raw_candidates)

    if angle is None:
        return {"error": "could not find needle"}

    # Determine which method the winning angle came from
    winning_method = min(raw_candidates, key=lambda x: _angle_diff(x[0], angle))[0]
    for a, c, m in candidates:
        if _angle_diff(a, angle) < _angle_diff(winning_method, angle):
            winning_method = m

    return {"angle": round(angle, 2), "confidence": round(confidence, 2), "method": str(winning_method)}
```

- [ ] **Step 4: Run tests**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_find_needle.py -v
```

Expected: 7 passed (some assertions may need lenience on synthetic images)

- [ ] **Step 5: Commit**

```bash
git add edge/gauge_reader/find_needle.py edge/tests/test_find_needle.py
git commit -m "feat: add multi-strategy needle detection with confidence voting"
```

---

### Task 6: Update gauge_reader __init__.py exports

**Files:**
- Modify: `edge/gauge_reader/__init__.py`

Add exports for new modules. Keep backward compat.

- [ ] **Step 1: Update exports**

Replace `edge/gauge_reader/__init__.py`:

```python
"""Gauge reader: analog gauge needle detection library."""

from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle_radial import (
    find_needle_angle as find_needle_angle_legacy,
    detect_scale_range, compute_variance_profile, learn_gap_params,
)
from gauge_reader.find_needle import find_needle_angle
from gauge_reader.draw import draw_needle
from gauge_reader.preprocess import preprocess, apply_clahe, bilateral_denoise
from gauge_reader.temporal import CenterTracker, AngleKalman
from gauge_reader.value_filter import ValueFilter


def angle_to_value(angle_deg, min_angle, max_angle, min_value, max_value):
    """Map needle angle to gauge value with wrap-around support.

    Returns value clamped to [min_value, max_value].
    """
    new_range = max_value - min_value
    if min_angle <= max_angle:
        denom = max_angle - min_angle
        if denom == 0:
            return min_value
        value = ((angle_deg - min_angle) * new_range) / denom + min_value
    else:
        denom = (360 - min_angle) + max_angle
        if denom == 0:
            return min_value
        if angle_deg >= min_angle:
            numer = angle_deg - min_angle
        else:
            numer = (360 - min_angle) + angle_deg
        value = (numer * new_range) / denom + min_value
    return max(min_value, min(max_value, value))
```

- [ ] **Step 2: Verify imports**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "
from gauge_reader import (find_gauge_center, find_gauge_center_legacy,
    find_needle_angle, find_needle_angle_legacy, draw_needle,
    preprocess, CenterTracker, AngleKalman, ValueFilter, angle_to_value)
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 3: Commit**

```bash
git add edge/gauge_reader/__init__.py
git commit -m "feat: update gauge_reader __init__.py with v2 exports"
```

---

### Task 7: Wire new pipeline into api.py

**Files:**
- Modify: `edge/app/api.py`

Replace `_run_detection()` with v2 pipeline, add config-driven fallback to legacy. All existing endpoints unchanged.

- [ ] **Step 1: Add new config defaults to `load_config()`**

In `api.py`, the `load_config()` function (lines 50-75), add new keys to defaults dict:

```python
defaults.setdefault("detect_method", "auto")
defaults.setdefault("use_clahe", True)
defaults.setdefault("use_difference_ref", False)
defaults.setdefault("overlay_fps", 4)
defaults.setdefault("center_ema", 0.3)
defaults.setdefault("angle_kalman_R", 0.1)
defaults.setdefault("angle_kalman_Q", 0.01)
```

Add after line 75 (after existing `defaults.setdefault("filter_window", 5)`).

- [ ] **Step 2: Add imports at top of api.py**

Add after the existing gauge_reader imports (after line 25):

```python
from gauge_reader.preprocess import preprocess
from gauge_reader.temporal import CenterTracker, AngleKalman
```

- [ ] **Step 3: Add temporal trackers to module globals**

Add after `_value_filter_lock` (after line 103):

```python
_center_tracker = CenterTracker()
_center_tracker_lock = threading.Lock()
_angle_kalman = AngleKalman()
_angle_kalman_lock = threading.Lock()
```

- [ ] **Step 4: Add helper to reinit temporal filters from config**

Add near `_reinit_filter` (after line 110):

```python
def _reinit_temporal(cfg):
    with _center_tracker_lock:
        _center_tracker.alpha = float(cfg.get("center_ema", 0.3))
    with _angle_kalman_lock:
        _angle_kalman.R = float(cfg.get("angle_kalman_R", 0.1))
        _angle_kalman.Q = float(cfg.get("angle_kalman_Q", 0.01))
```

- [ ] **Step 5: Rewrite `_run_detection()` to use v2 pipeline**

Replace the existing `_run_detection` function (lines 349-391) with:

```python
def _run_detection(frame, cfg):
    """Detect gauge: v2 pipeline with legacy fallback via detect_method config."""
    method = cfg.get("detect_method", "auto")
    use_clahe = cfg.get("use_clahe", True)

    h_orig, w_orig = frame.shape[:2]
    if max(w_orig, h_orig) > _DETECT_USE_W:
        scale = _DETECT_USE_W / max(w_orig, h_orig)
        small = cv2.resize(frame, (int(w_orig * scale), int(h_orig * scale)),
                           interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
        small = frame

    # Preprocess
    if method != "radial":
        proc = preprocess(small, clahe=use_clahe, denoise=True)
    else:
        proc = small

    # Center detection
    if method == "radial":
        center_result = find_gauge_center_legacy(proc)
        if center_result is None:
            return {"error": "could not find gauge center"}
        cx, cy, radius = center_result
        center_conf = 0.5
    else:
        with _center_tracker_lock:
            prev = _center_tracker.get() if _center_tracker.initialized else None
        center_result = find_gauge_center(proc, prev_center=prev,
                                          ema_alpha=float(cfg.get("center_ema", 0.3)),
                                          use_clahe=use_clahe)
        if center_result is None:
            return {"error": "could not find gauge center"}
        cx, cy, radius, center_conf = center_result
        with _center_tracker_lock:
            _center_tracker.update(cx, cy, radius)

    cy_adjusted = cy + int(cfg["center_offset_y"])

    # Needle detection
    if method == "radial":
        angle_result = find_needle_angle_legacy(
            proc, cx, cy_adjusted, radius,
            inner_ratio=float(cfg["inner_ratio"]),
            outer_ratio=float(cfg["outer_ratio"]),
            blur_kernel=int(cfg["blur_kernel"]),
            threshold_block=int(cfg["threshold_block"]),
            threshold_c=int(cfg["threshold_c"]),
        )
        if isinstance(angle_result, dict) and "error" in angle_result:
            return angle_result
        angle_deg = float(angle_result) if not isinstance(angle_result, dict) else float(angle_result["angle"])
    else:
        angle_result = find_needle_angle(
            proc, cx, cy_adjusted, radius,
            inner_ratio=float(cfg["inner_ratio"]),
            outer_ratio=float(cfg["outer_ratio"]),
            blur_kernel=int(cfg["blur_kernel"]),
            threshold_block=int(cfg["threshold_block"]),
            threshold_c=int(cfg["threshold_c"]),
            method=method,
            background_ref=None,
            min_angle=float(cfg["min_angle"]),
            max_angle=float(cfg["max_angle"]),
            use_clahe=use_clahe,
        )
        if "error" in angle_result:
            return angle_result
        angle_deg = float(angle_result["angle"])

    # Temporal angle filter
    if method != "radial":
        with _angle_kalman_lock:
            angle_deg = _angle_kalman.update(angle_deg)

    # Upscale coords
    inv = 1.0 / scale if scale != 1.0 else 1.0
    cx_out = int(cx * inv)
    cy_out = int(cy_adjusted * inv)
    radius_out = int(radius * inv)

    min_a, max_a = float(cfg["min_angle"]), float(cfg["max_angle"])
    min_v, max_v = float(cfg["min_value"]), float(cfg["max_value"])
    value = angle_to_value(angle_deg, min_a, max_a, min_v, max_v)

    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx_out, "y": cy_out, "radius": radius_out},
        "error": None,
        "w": w_orig, "h": h_orig,
    }
```

- [ ] **Step 6: Update `_reinit_filter` callchain**

In `set_stream_detect_config()` (line 309), add after `_reinit_filter(merged)`:

```python
    _reinit_temporal(merged)
```

In `update_config()` (line 546), add after `_reinit_filter(cfg)`:

```python
    _reinit_temporal(cfg)
```

- [ ] **Step 7: Verify api.py imports resolve**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
from app.api import app
print('api.py loads OK')
"
```

- [ ] **Step 8: Commit**

```bash
git add edge/app/api.py
git commit -m "feat: wire v2 detection pipeline into api.py with config-driven fallback"
```

---

### Task 8: Wire new pipeline into push_readings.py

**Files:**
- Modify: `edge/push_readings.py`

Update `detect_gauge()` to use v2 pipeline when configured.

- [ ] **Step 1: Update imports in push_readings.py**

Replace the current imports (lines 24-27):

```python
from gauge_reader import angle_to_value
from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle_radial import find_needle_angle as find_needle_angle_legacy, draw_needle
from gauge_reader.find_needle import find_needle_angle
from gauge_reader.preprocess import preprocess
from gauge_reader.temporal import CenterTracker, AngleKalman
from gauge_reader.value_filter import ValueFilter
```

- [ ] **Step 2: Replace `detect_gauge()` function**

Replace lines 67-115 with:

```python
def detect_gauge(img, config, center_tracker=None, angle_kalman=None):
    method = config.get("detect_method", "auto")
    use_clahe = config.get("use_clahe", True)

    h_orig, w_orig = img.shape[:2]
    if max(w_orig, h_orig) > _DETECT_USE_W:
        scale = _DETECT_USE_W / max(w_orig, h_orig)
        small = cv2.resize(img, (int(w_orig * scale), int(h_orig * scale)),
                             interpolation=cv2.INTER_AREA)
    else:
        scale = 1.0
        small = img

    # Preprocess
    if method != "radial":
        proc = preprocess(small, clahe=use_clahe, denoise=True)
    else:
        proc = small

    # Center
    if method == "radial":
        center_result = find_gauge_center_legacy(proc)
        if center_result is None:
            return None, "could not find gauge center"
        cx, cy, radius = center_result
    else:
        prev = center_tracker.get() if (center_tracker and center_tracker.initialized) else None
        center_result = find_gauge_center(proc, prev_center=prev,
                                          ema_alpha=float(config.get("center_ema", 0.3)),
                                          use_clahe=use_clahe)
        if center_result is None:
            return None, "could not find gauge center"
        cx, cy, radius, _ = center_result
        if center_tracker:
            center_tracker.update(cx, cy, radius)

    cy += int(config["center_offset_y"])

    # Needle
    if method == "radial":
        angle_deg = find_needle_angle_legacy(
            proc, cx, cy, radius,
            inner_ratio=float(config["inner_ratio"]),
            outer_ratio=float(config["outer_ratio"]),
            blur_kernel=int(config["blur_kernel"]),
            threshold_block=int(config["threshold_block"]),
            threshold_c=int(config["threshold_c"]),
        )
    else:
        result = find_needle_angle(
            proc, cx, cy, radius,
            inner_ratio=float(config["inner_ratio"]),
            outer_ratio=float(config["outer_ratio"]),
            blur_kernel=int(config["blur_kernel"]),
            threshold_block=int(config["threshold_block"]),
            threshold_c=int(config["threshold_c"]),
            method=method,
            background_ref=None,
            min_angle=float(config["min_angle"]),
            max_angle=float(config["max_angle"]),
            use_clahe=use_clahe,
        )
        if "error" in result:
            return None, result["error"]
        angle_deg = float(result["angle"])

    if method != "radial" and angle_kalman:
        angle_deg = angle_kalman.update(angle_deg)

    # Upscale
    inv = 1.0 / scale if scale != 1.0 else 1.0
    cx_out = int(cx * inv)
    cy_out = int(cy * inv)
    radius_out = int(radius * inv)

    value = angle_to_value(angle_deg, float(config["min_angle"]), float(config["max_angle"]),
                           float(config["min_value"]), float(config["max_value"]))

    annotated = draw_needle(img.copy(), cx_out, cy_out, radius_out, angle_deg,
                            inner_ratio=float(config["inner_ratio"]),
                            outer_ratio=float(config["outer_ratio"]),
                            min_angle=float(config["min_angle"]),
                            max_angle=float(config["max_angle"]))
    _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx_out, "y": cy_out, "radius": radius_out},
        "annotated_image": annotated_b64,
    }, None
```

- [ ] **Step 3: Update `do_reading()` to pass temporal trackers**

Update `do_reading()` (line 140) to accept and pass trackers. Replace function:

```python
def do_reading(config, camera_id=0, value_filter=None, center_tracker=None, angle_kalman=None):
    try:
        frame = capture_frame(camera_id)
    except RuntimeError as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture error: {e}")
        return

    result, err = detect_gauge(frame, config, center_tracker=center_tracker, angle_kalman=angle_kalman)
    if err or result is None:
        print(f"[{time.strftime('%H:%M:%S')}] Detection error: {err}")
        return

    raw_value = result["value"]
    filtered = value_filter.add(raw_value) if value_filter is not None else raw_value
    if filtered != raw_value:
        print(f"[{time.strftime('%H:%M:%S')}] Spike rejected: {raw_value}→{filtered:.2f}")

    payload = {
        "point": config["point"],
        "value": round(filtered, 2),
        "angle": result["angle"],
        "annotated_image": result["annotated_image"],
    }

    resp, err = push_to_server(payload, config)
    if err:
        print(f"[{time.strftime('%H:%M:%S')}] Push error: {err}")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] Pushed {config['point']} = {payload['value']}  server: {resp.get('status', '?')}")
```

- [ ] **Step 4: Update `main()` to create trackers and pass them**

Update `main()` (line 171) — add tracker creation after `vf = ValueFilter()`:

```python
    vf = ValueFilter()
    ct = CenterTracker(ema_alpha=float(config.get("center_ema", 0.3)))
    ak = AngleKalman(R=float(config.get("angle_kalman_R", 0.1)),
                     Q=float(config.get("angle_kalman_Q", 0.01)))
    while True:
        do_reading(config, args.camera, value_filter=vf, center_tracker=ct, angle_kalman=ak)
```

- [ ] **Step 5: Verify**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "import push_readings; print('OK')"
```

- [ ] **Step 6: Commit**

```bash
git add edge/push_readings.py
git commit -m "feat: wire v2 detection pipeline into push_readings.py"
```

---

### Task 9: Frontend — client cam canvas overlay + detection UI

**Files:**
- Modify: `edge/app/static/index.html`

Add client cam detection polling loop, canvas overlay drawing, smoothing config UI controls. No new endpoints needed — reuses existing `/detect`.

- [ ] **Step 1: Add smoothing config card HTML**

Add after the "Detection" card (after line 771 `</div>` for that card) in `index.html`:

```html
    <div class="card">
      <div class="card-title">Smoothing v2 <span class="badge">TEMPORAL</span></div>
      <div class="field-row three">
        <div class="field-group"><label>Center EMA</label><input id="center_ema" type="number" step="0.05" min="0.05" max="0.95" value="0.30"></div>
        <div class="field-group"><label>Kalman R</label><input id="angle_kalman_R" type="number" step="0.01" min="0.01" max="5" value="0.10"><div class="help">measurement noise</div></div>
        <div class="field-group"><label>Kalman Q</label><input id="angle_kalman_Q" type="number" step="0.001" min="0.001" max="1" value="0.01"><div class="help">process noise</div></div>
      </div>
    </div>
```

- [ ] **Step 2: Add detect method selector to Detection card**

Add above the existing `field-row three` for blur_kernel in the Detection card (before line 766):

```html
      <div class="field-row single">
        <div class="field-group">
          <label>Method</label>
          <select id="detect_method">
            <option value="auto">Auto (multi-strategy vote)</option>
            <option value="line">Line (Hough)</option>
            <option value="radial">Radial (legacy)</option>
            <option value="diff">Difference</option>
          </select>
        </div>
      </div>
```

- [ ] **Step 3: Add CLAHE toggle to Detection card**

Add after the detect_method field-row:

```html
      <div class="field-row single">
        <div class="field-group">
          <label style="display:flex;align-items:center;gap:8px">
            <input type="checkbox" id="use_clahe" checked style="width:auto">
            CLAHE lighting normalization
          </label>
        </div>
      </div>
```

- [ ] **Step 4: Update `getFormValues()` to include new fields**

Add to the fields array in `getFormValues()`:

```javascript
'detect_method','use_clahe','use_difference_ref','overlay_fps','center_ema','angle_kalman_R','angle_kalman_Q',
```

- [ ] **Step 5: Update config loading to set new fields**

Add after `loadConfig()` — handle checkbox for `use_clahe`:

```javascript
    const claheEl = q('use_clahe');
    if (claheEl && c.use_clahe !== undefined) claheEl.checked = c.use_clahe;
```

- [ ] **Step 6: Add client cam overlay detection loop**

Add these functions to the `<script>` block:

```javascript
let overlayTimer = null;
let overlayActive = false;
let overlayFps = 4;

function startOverlay() {
  if (overlayActive) return;
  overlayActive = true;
  overlayFps = parseFloat(q('overlay_fps')?.value) || 4;
  pollOverlay();
}

function stopOverlay() {
  overlayActive = false;
  if (overlayTimer) { clearTimeout(overlayTimer); overlayTimer = null; }
  clearCanvas();
}

async function pollOverlay() {
  if (!overlayActive) return;
  if (cameraMode !== 'client' || !streamActive) {
    stopOverlay();
    return;
  }
  try {
    const video = q('feed-video');
    if (!video || !video.videoWidth) { overlayTimer = setTimeout(pollOverlay, 1000 / overlayFps); return; }
    // Capture frame
    const c = document.createElement('canvas');
    c.width = video.videoWidth;
    c.height = video.videoHeight;
    const ctx = c.getContext('2d');
    ctx.drawImage(video, 0, 0);
    const blob = await new Promise(resolve => c.toBlob(resolve, 'image/jpeg', 0.7));
    // POST to /detect
    const form = new FormData();
    form.append('image', blob, 'frame.jpg');
    ['min_angle','max_angle','min_value','max_value','center_offset_y',
     'inner_ratio','outer_ratio','blur_kernel','threshold_block','threshold_c',
     'detect_method','use_clahe'].forEach(id => {
      const el = q(id);
      if (el) form.append(id, el.type === 'checkbox' ? (el.checked ? '1' : '0') : el.value);
    });
    form.append('need_annotation', 'false');
    const r = await fetch(API + '/detect', { method: 'POST', body: form });
    if (r.ok) {
      const d = await r.json();
      if (d && d.center && d.angle !== undefined && !d.error) {
        drawOverlay(d);
        updateOverlayHUD(d);
      }
    }
  } catch(e) { /* silent — next poll will retry */ }
  overlayTimer = setTimeout(pollOverlay, 1000 / overlayFps);
}

function drawOverlay(d) {
  const canvas = q('feed-canvas');
  const body = q('feed-body');
  canvas.width = body.clientWidth;
  canvas.height = body.clientHeight;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const ctr = d.center;
  const video = q('feed-video');
  const vw = video.videoWidth || 640;
  const vh = video.videoHeight || 480;
  const cw = canvas.width;
  const ch = canvas.height;

  // Letterbox mapping
  const videoAspect = vw / vh;
  const canvasAspect = cw / ch;
  let renderW, renderH, offX, offY;
  if (videoAspect > canvasAspect) {
    renderW = cw;
    renderH = cw / videoAspect;
    offX = 0;
    offY = (ch - renderH) / 2;
  } else {
    renderH = ch;
    renderW = ch * videoAspect;
    offY = 0;
    offX = (cw - renderW) / 2;
  }
  const sx = renderW / vw;
  const sy = renderH / vh;

  const cx = offX + ctr.x * sx;
  const cy = offY + ctr.y * sy;
  const radius = ctr.radius * sx;

  // Gauge circle
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(225,29,72,0.8)';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Center dot
  ctx.beginPath();
  ctx.arc(cx, cy, 4, 0, Math.PI * 2);
  ctx.fillStyle = '#e11d48';
  ctx.fill();

  // Needle line
  const angleRad = d.angle * Math.PI / 180;
  const nx = cx + radius * 0.85 * Math.cos(angleRad);
  const ny = cy + radius * 0.85 * Math.sin(angleRad);
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(nx, ny);
  ctx.strokeStyle = '#e11d48';
  ctx.lineWidth = 2.5;
  ctx.shadowColor = 'rgba(225,29,72,0.4)';
  ctx.shadowBlur = 10;
  ctx.stroke();
  ctx.shadowBlur = 0;
}

function updateOverlayHUD(d) {
  q('hud-value').textContent = d.value !== undefined ? d.value : '--';
  q('hud-value').className = 'hud-value gold';
  q('hud-angle').textContent = d.angle !== undefined ? d.angle + ' deg' : '--';
  q('hud-angle').className = 'hud-value teal';
  q('hud-center').textContent = d.center ? d.center.x + ',' + d.center.y : '--';
  q('hud-status').textContent = 'Overlay';
  q('hud-status').className = 'hud-value green';
}
```

- [ ] **Step 7: Hook overlay into stream start/stop**

In `startClientStream()`, add after `streamActive = true`:

```javascript
    startOverlay();
```

In `stopStream()`, add at top:

```javascript
  stopOverlay();
```

In `setCameraMode()`, add before `hideResult()`:

```javascript
  stopOverlay();
```

- [ ] **Step 8: Update `stopStreamDetection()` for edge cam detect stop**

When detect stops on edge cam, also stop overlay. In `stopStreamDetection()`, after clearing timer:

```javascript
  // Canvas overlay stops when edge detect stops
  clearCanvas();
```

- [ ] **Step 9: Update `loadConfig()` for checkbox fields**

In the `loadConfig()` function, after the `for (const k of Object.keys(c))` loop that sets values, add:

```javascript
    const checkboxFields = ['use_clahe'];
    checkboxFields.forEach(k => {
      const el = q(k);
      if (el && c[k] !== undefined) el.checked = !!c[k];
    });
```

- [ ] **Step 10: Verify HTML is valid**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "
with open('app/static/index.html') as f:
    content = f.read()
assert '<html' in content and '</html>' in content
assert 'startOverlay' in content
print('HTML structure OK')
"
```

- [ ] **Step 11: Commit**

```bash
git add edge/app/static/index.html
git commit -m "feat: add client cam canvas overlay + v2 smoothing UI controls"
```

---

### Task 10: Update config.json.example + read_gauge.py CLI

**Files:**
- Modify: `edge/config.json.example`
- Modify: `edge/gauge_reader/read_gauge.py`

- [ ] **Step 1: Add new keys to config.json.example**

Add after `"filter_window": 5`:

```json
  "detect_method": "auto",
  "use_clahe": true,
  "use_difference_ref": false,
  "overlay_fps": 4,
  "center_ema": 0.3,
  "angle_kalman_R": 0.1,
  "angle_kalman_Q": 0.01,
```

- [ ] **Step 2: Update read_gauge.py to accept new params**

Replace `read_gauge.py`'s `main()` with updated CLI that accepts new args and uses new pipeline. Replace the `main()` function (lines 23-101):

Wait — `read_gauge.py` is standalone CLI. It should work without config.json. Update `main()` to add new args and use v2 pipeline:

Replace `main()` function with:

```python
def main():
    parser = argparse.ArgumentParser(description="Read analog gauge value from image.")
    parser.add_argument("image_path", help="Path to gauge image file")
    parser.add_argument("--min-value", type=float, default=0.0, help="Minimum gauge value")
    parser.add_argument("--max-value", type=float, default=100.0, help="Maximum gauge value")
    parser.add_argument("--min-angle", type=float, default=45.0, help="Angle at minimum value (degrees)")
    parser.add_argument("--max-angle", type=float, default=315.0, help="Angle at maximum value (degrees)")
    parser.add_argument("--center-offset-y", type=float, default=0.0)
    parser.add_argument("--inner-ratio", type=float, default=0.60)
    parser.add_argument("--outer-ratio", type=float, default=0.80)
    parser.add_argument("--blur-kernel", type=int, default=5)
    parser.add_argument("--threshold-block", type=int, default=0)
    parser.add_argument("--threshold-c", type=int, default=5)
    parser.add_argument("--method", default="auto", choices=["auto", "line", "radial", "diff"])
    parser.add_argument("--no-clahe", action="store_true", help="Disable CLAHE preprocessing")
    parser.add_argument("--save-annotated", help="Save annotated image to this path")
    args = parser.parse_args()

    img = cv2.imread(args.image_path)
    if img is None:
        print(json.dumps({"error": f"cannot read image: {args.image_path}"}))
        sys.exit(1)

    # Preprocess
    use_clahe = not args.no_clahe
    if args.method != "radial":
        proc = preprocess(img, clahe=use_clahe, denoise=True)
    else:
        proc = img

    # Center
    if args.method == "radial":
        center_result = find_gauge_center_legacy(proc)
        if center_result is None:
            print(json.dumps({"error": "could not find gauge center"}))
            sys.exit(1)
        cx, cy, radius = center_result
    else:
        center_result = find_gauge_center(proc, prev_center=None, use_clahe=use_clahe)
        if center_result is None:
            print(json.dumps({"error": "could not find gauge center"}))
            sys.exit(1)
        cx, cy, radius, _ = center_result

    cy += int(args.center_offset_y)

    # Needle
    if args.method == "radial":
        angle_deg = find_needle_angle_legacy(proc, cx, cy, radius,
                                             inner_ratio=args.inner_ratio,
                                             outer_ratio=args.outer_ratio,
                                             blur_kernel=args.blur_kernel,
                                             threshold_block=args.threshold_block,
                                             threshold_c=args.threshold_c)
    else:
        result = find_needle_angle(proc, cx, cy, radius,
                                   inner_ratio=args.inner_ratio,
                                   outer_ratio=args.outer_ratio,
                                   blur_kernel=args.blur_kernel,
                                   threshold_block=args.threshold_block,
                                   threshold_c=args.threshold_c,
                                   method=args.method,
                                   background_ref=None,
                                   min_angle=args.min_angle,
                                   max_angle=args.max_angle,
                                   use_clahe=use_clahe)
        if "error" in result:
            print(json.dumps(result))
            sys.exit(1)
        angle_deg = float(result["angle"])

    # angle -> value
    value = angle_to_value(angle_deg, args.min_angle, args.max_angle,
                           args.min_value, args.max_value)

    annotated_path = None
    if args.save_annotated:
        annotated = draw_needle(img.copy(), cx, cy, radius, angle_deg,
                                inner_ratio=args.inner_ratio,
                                outer_ratio=args.outer_ratio,
                                min_angle=args.min_angle,
                                max_angle=args.max_angle)
        cv2.imwrite(args.save_annotated, annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
        annotated_path = args.save_annotated

    print(json.dumps({
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx, "y": cy, "radius": radius},
        "annotated_image": annotated_path,
        "error": None,
    }))
```

Update imports at top of `read_gauge.py` to add:

```python
from gauge_reader import angle_to_value
from gauge_reader.preprocess import preprocess
from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle_radial import find_needle_angle as find_needle_angle_legacy
from gauge_reader.find_needle import find_needle_angle
from gauge_reader.draw import draw_needle
```

Replace the old imports completely (lines 19-21).

- [ ] **Step 3: Verify CLI loads**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "from gauge_reader.read_gauge import main; print('CLI OK')"
```

- [ ] **Step 4: Commit**

```bash
git add edge/config.json.example edge/gauge_reader/read_gauge.py
git commit -m "feat: update config example and CLI for v2 pipeline params"
```

---

### Task 11: Integration test — full pipeline on synthetic gauge

**Files:**
- Create: `edge/tests/test_integration.py`

End-to-end test: synthetic gauge → detect → verify output structure and angle accuracy.

- [ ] **Step 1: Write integration test**

```python
import numpy as np
import cv2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gauge_reader.find_gauge_center import find_gauge_center
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

    # Tick marks every 10°
    for a in range(0, 360, 10):
        rad = np.deg2rad(a)
        r_start = radius - 8
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
    cx, cy, radius, conf = center
    assert conf > 0.3

    needle = find_needle_angle(proc, cx, cy, radius,
                               inner_ratio=0.30, outer_ratio=0.80,
                               blur_kernel=0, threshold_block=0, threshold_c=0,
                               method="auto", use_clahe=False)
    assert "error" not in needle, f"needle detection failed: {needle}"
    detected_angle = needle["angle"]
    diff = abs(detected_angle - 60)
    assert diff < 15, f"Angle off by {diff:.1f}°, detected {detected_angle}"


def test_full_pipeline_synthetic_150deg():
    img = make_realistic_gauge(angle_deg=150)
    proc = preprocess(img, clahe=True, denoise=True)
    center = find_gauge_center(proc, use_clahe=False)
    assert center is not None
    cx, cy, radius, conf = center
    needle = find_needle_angle(proc, cx, cy, radius,
                               inner_ratio=0.30, outer_ratio=0.80,
                               method="auto", use_clahe=False)
    diff = abs(needle["angle"] - 150)
    assert diff < 15, f"Angle off by {diff:.1f}°"


def test_draw_needle_returns_image():
    img = make_realistic_gauge(angle_deg=45)
    annotated = draw_needle(img.copy(), 320, 240, 150, 45,
                            inner_ratio=0.30, outer_ratio=0.80,
                            min_angle=30, max_angle=330)
    assert annotated.shape == img.shape
    assert annotated is not img  # copy


def test_legacy_radial_works():
    img = make_realistic_gauge(angle_deg=90)
    center = find_gauge_center(img, use_clahe=False)
    assert center is not None
    cx, cy, radius, conf = center
    needle = find_needle_angle(img, cx, cy, radius,
                               method="radial", use_clahe=False)
    assert "error" not in needle
    assert abs(needle["angle"] - 90) < 20
    assert needle["method"] == "radial"


def test_angle_to_value_wrap():
    # min_angle=315, max_angle=45 → wraps around 0
    v = angle_to_value(0, 315, 45, 0, 100)
    assert 45 < v < 55, f"Expected ~50, got {v}"


def test_angle_to_value_normal():
    v = angle_to_value(135, 45, 315, 0, 10)
    assert 3 < v < 4, f"Expected ~3.33, got {v}"
```

- [ ] **Step 2: Run integration tests**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/test_integration.py -v
```

Expected: 7 passed (angle tolerances generous for synthetic images)

- [ ] **Step 3: Commit**

```bash
git add edge/tests/test_integration.py
git commit -m "test: add integration tests for full v2 detection pipeline"
```

---

### Task 12: Run full test suite + final verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run all tests**

```bash
cd /home/ihsan/opcv-1/edge && python3 -m pytest tests/ -v
```

Expected: all tests from Tasks 2-5 + 11 pass

- [ ] **Step 2: Verify backward compat — import legacy modules**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle, detect_scale_range
from gauge_reader.find_gauge_center import find_gauge_center_legacy
print('Legacy imports OK')
"
```

- [ ] **Step 3: Verify api.py loads clean**

```bash
cd /home/ihsan/opcv-1/edge && python3 -c "
import sys, os
sys.path.insert(0, '.')
from app.api import app
# Verify routes
routes = [r.path for r in app.routes]
for ep in ['/api/stream', '/api/one-shot', '/detect', '/api/config', '/api/stream-detect-config', '/health']:
    assert ep in routes, f'{ep} missing'
print('All routes present')
"
```

- [ ] **Step 4: Commit (if any test fixups needed)**

```bash
git status
```

---

### Task 13: Deploy to Orange Pi

- [ ] **Step 1: Push all commits to origin**

```bash
git push origin main
```

- [ ] **Step 2: SSH into edge device, rebuild**

```bash
sshpass -p orangepi ssh root@10.8.0.4 "cd /root/opcv-1 && git pull && cd /root/edge && docker compose up -d --build"
```

- [ ] **Step 3: Verify health endpoint**

```bash
curl -k https://10.8.0.4:8765/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Test client cam overlay in browser**

Open `https://10.8.0.4:8765` in browser, switch to Client Cam tab, grant camera permission, verify canvas overlay draws needle annotations on live video.

- [ ] **Step 5: Test edge cam detect with v2 pipeline**

In config: set method=auto, CLAHE enabled. Start edge cam stream + detect. Verify HUD shows stable readings.

- [ ] **Step 6: Test legacy mode unchanged**

Set method=radial. Verify behavior identical to pre-v2 behavior.
