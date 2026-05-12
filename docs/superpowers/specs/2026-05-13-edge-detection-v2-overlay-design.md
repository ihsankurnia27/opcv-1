# Edge Detection Pipeline v2 + Universal Overlay

Date: 2026-05-13
Status: Design

## Goal

Two-part improvement to the edge gauge detection system:

1. **Universal overlay** — draw needle/gauge annotations on live video feed from both Edge Cam and Client Cam modes
2. **Detection pipeline rewrite** — replace fragile "darkest radial ray" method with multi-strategy voting for center and needle detection

## Current State

### What works
- Edge Cam + Detect ON: annotated JPEGs streamed via MJPEG (`draw_needle()` burns into frame)
- Edge Cam + Detect OFF: raw frames only
- One-shot edge cam: annotated image returned
- Client cam one-shot: capture frame → POST to `/detect` → annotated image shown as result
- HUD: HTML `<div>` overlay showing value/angle/center numbers

### What's missing
- Client cam live feed has NO annotation overlay — raw `<video>` element only
- No common overlay path between edge cam and client cam

### Detection weaknesses (root cause analysis)

1. **Center detection fragile** — SimpleBlobDetector finds dark blobs. Analog gauges often have white/silver center pins. HoughCircles fallback expects near-perfect circles; gauge bezels elliptical from camera angle, broken by shadows, confused by tick mark ring.

2. **"Darkest ray" is the only needle signal** — radial sampling picks angle with minimum mean intensity. Tick marks are dark too. `inner_ratio`/`outer_ratio` try to exclude them, but on small gauges or wide tick marks, needle signal buried in tick noise. A shadow across the annulus can produce a darker ray than the real needle.

3. **No geometric needle detection** — never looks for the needle as a physical line/structure. Just pixel intensity along rays.

4. **No lighting normalization** — no CLAHE or histogram equalization. Dark corners, uneven illumination, backlit gauges degrade both center and needle detection.

5. **No temporal consistency** — each frame independently detected. No tracking of center position or needle angle between frames. Jitter comes from per-frame noise, not actual needle movement.

## Design

### Architecture

```
Camera Frame
  ↓
[1] Preprocessing (CLAHE + bilateral + optional background subtract)
  ↓
[2] Center Detection (Canny → HoughCircles → contour → temporal EMA)
  ↓
[3] Needle Detection (multi-strategy: line + difference + radial → confidence vote)
  ↓
[4] Angle → Value (shared angle_to_value)
  ↓
[5] Temporal Filter (EMA center + Kalman angle + ValueFilter on output)
  ↓
[6] Overlay Render ──→ Edge Cam: burn into JPEG
                   ──→ Client Cam: JS canvas overlay
```

### Step 1 — Preprocessing (`gauge_reader/preprocess.py`)

New module. Functions:
- `to_lab_l_channel(img)` — convert BGR → LAB, extract L channel (perceptual luminance)
- `apply_clahe(gray, clip=2.0, tile=8)` — CLAHE for lighting normalization
- `bilateral_denoise(gray)` — edge-preserving blur: `cv2.bilateralFilter(gray, 5, 75, 75)`
- `build_background_model(frames)` — median of N frames as reference (optional)
- `subtract_background(gray, ref)` — absolute difference, Otsu threshold

### Step 2 — Center Detection (`gauge_reader/find_gauge_center.py`)

Rewrite. Three strategies in cascade:

| Strategy | Method | When |
|----------|--------|------|
| A: Edge+Hough | Canny → HoughCircles with `dp=1.2, minDist, param1=100, param2=50` + gradient direction voting | Always try first |
| B: Contour circularity | Find largest contour with circularity >0.7 → `minEnclosingCircle` | Fallback if A fails |
| C: Temporal prior | Use EMA-predicted center from previous frames | Fallback if A+B fail |

Temporal smoothing: EMA with configurable alpha on cx, cy, radius.

New function signature:
```python
def find_gauge_center(image, prev_center=None, ema_alpha=0.3, use_clahe=True) -> tuple | None
```

Returns `(cx, cy, radius, confidence)` where confidence is 0.0-1.0.

### Step 3 — Needle Detection (`gauge_reader/find_needle.py`)

New module. Three independent strategies, confidence-weighted vote.

**Strategy A: Line Detection (primary)**
1. Canny edge on annulus ROI (inner_ratio to outer_ratio ring)
2. HoughLinesP with tuned params
3. Filter lines by geometry:
   - Extension must pass within `center_tolerance` px of gauge center
   - Line length within `[radius * inner_ratio * 0.3, radius * outer_ratio * 1.5]`
   - Angle within `[min_angle - 5, max_angle + 5]` if calibrated
4. Surviving lines: median angle → confidence based on line count agreement
5. Sub-degree refinement: fit line through edge pixels via linear regression

**Strategy B: Background Difference (optional)**
1. Require calibrated reference image (no needle, or needle at zero)
2. `cv2.absdiff(current, reference)` → threshold → finds needle region
3. PCA of needle pixel coordinates → principal axis = needle angle
4. Works best when camera fixed on tripod (edge cam)

**Strategy C: Radial Dark Ray (legacy fallback)**
1. Current method preserved as-is
2. Lowest confidence weight in vote

**Vote logic:**
```
candidates = [(angle_a, conf_a), (angle_b, conf_b), (angle_c, conf_c)]
groups = cluster by ±5° agreement
if largest group has >=2 strategies:
    weighted_average(largest group angles, weights=confidences)
elif any strategy reported:
    use that angle with reduced confidence
else:
    error
```

New function signature:
```python
def find_needle_angle(image, cx, cy, radius, inner_ratio, outer_ratio,
                      blur_kernel, threshold_block, threshold_c,
                      method="auto", background_ref=None,
                      min_angle=None, max_angle=None,
                      use_clahe=True) -> dict
```

Returns `{"angle": float, "confidence": float, "method": str}`.

### Step 4 — Angle to Value

No change. Reuse existing `gauge_reader/__init__.py:angle_to_value()`.

### Step 5 — Temporal Stability (`gauge_reader/temporal.py`)

New module.

**Center tracker:**
- EMA on (cx, cy, radius) — smooths per-frame center jitter
- Alpha configurable, default 0.3 (higher = less smoothing)

**Angle filter:**
- Simple 1D Kalman filter (constant position model)
- Parameters: `R` (measurement noise, default 0.1), `Q` (process noise, default 0.01)
- Rejects single-frame spikes, tracks smooth needle movement

**Value filter:**
- Keep existing `ValueFilter` (EMA + median + spike rejection)

### Step 6 — Overlay System

**Edge Cam (backend, api.py):**
No structural change. Reader loop already runs detection → draws needle → encodes JPEG. Wire new detection functions replacing `_run_detection`. Annotated frames continue through existing MJPEG stream path.

**Client Cam (frontend, index.html):**
New JavaScript canvas overlay loop:

1. Grab video frame: draw `<video>` to hidden `<canvas>`, extract as JPEG blob
2. POST to `/detect` with calibration params (reuses existing endpoint)
3. Parse `{angle, value, center}`
4. Draw overlay on visible `<canvas>` positioned absolutely over `<video>`:
   - Gauge center dot
   - Needle line from center at detected angle
   - Min/max angle reference lines
   - Value text
5. Loop at configurable rate (default 4 fps, 250ms interval)

No new backend endpoint required. `/detect` already handles uploaded frames with full calibration params.

### Config Keys (config.json)

New keys with defaults:

```json
{
  "detect_method": "auto",
  "use_clahe": true,
  "use_difference_ref": false,
  "overlay_fps": 4,
  "center_ema": 0.3,
  "angle_kalman_R": 0.1,
  "angle_kalman_Q": 0.01
}
```

All existing keys unchanged. `detect_method: "radial"` preserves exact legacy behavior.

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `gauge_reader/preprocess.py` | New | CLAHE, bilateral filter, background subtraction |
| `gauge_reader/temporal.py` | New | EMA center tracker + 1D Kalman angle filter |
| `gauge_reader/find_gauge_center.py` | Rewrite | Canny+Hough+contour cascade with temporal prior |
| `gauge_reader/find_needle.py` | New | Multi-strategy needle detection with voting |
| `gauge_reader/draw.py` | New | Extracted `draw_needle()` from `find_needle_radial.py` |
| `gauge_reader/__init__.py` | Update | Export new public functions, keep `angle_to_value` |
| `gauge_reader/find_needle_radial.py` | Keep | Legacy fallback, import from `find_needle.py` |
| `app/api.py` | Update | Wire new pipeline, `use_legacy` config flag |
| `app/static/index.html` | Update | Canvas overlay, client cam detection loop, smoothing controls |
| `push_readings.py` | Update | Wire new pipeline |
| `gauge_reader/read_gauge.py` | Update | CLI args for new params |
| `config.json.example` | Update | Add new keys with documented defaults |

### Backward Compatibility

- `detect_method: "radial"` uses legacy code path exactly as before
- All existing config keys preserved with same defaults
- Old `find_gauge_center` and `find_needle_radial` modules kept, not deleted
- `/detect` endpoint signature unchanged
- `/api/stream` MJPEG path unchanged
- Push readings payload to server unchanged

### Testing

- Unit: `preprocess.py` (CLAHE output range, bilateral preserves edges)
- Unit: `temporal.py` (EMA convergence, Kalman step)
- Unit: `find_needle.py` (vote logic, cluster grouping)
- Integration: end-to-end on sample images with known angles
- Manual: client cam overlay on desktop browser, edge cam on Orange Pi
- Regression: `detect_method=radial` produces identical results to current code

### Rollout

1. Implement new modules (`preprocess.py`, `temporal.py`, `find_needle.py`, `draw.py`)
2. Rewrite `find_gauge_center.py`
3. Wire into `api.py` behind config flag
4. Frontend: canvas overlay + detection poll loop
5. Deploy to Orange Pi, test with real gauges
6. Tune params on real data
