# Adjustable Circle Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable users to tune circle detection parameters (Hough sensitivity, circularity, etc.) via the UI to handle challenging lighting and different gauge sizes.

**Architecture:** Update the detection engine to accept dynamic parameters, expose these through the FastAPI configuration system, and add controls to the MD3-styled frontend.

**Tech Stack:** Python (OpenCV, FastAPI), JavaScript (Vanilla), HTML/CSS (MD3).

---

### Task 1: Update Detection Engine

**Files:**
- Modify: `edge/gauge_reader/find_gauge_center.py`
- Test: `edge/tests/test_find_gauge_center.py`

- [ ] **Step 1: Update `_hough_circles` and `_contour_circularity` signatures**
Modify the internal functions to accept parameters instead of using constants.

```python
def _hough_circles(gray, image_w, image_h, dp=1.2, param1=100, param2=50, min_dist_ratio=0.3, min_radius_ratio=0.05, max_radius_ratio=0.45):
    edges = cv2.Canny(gray, 50, param1) # Using param1 for Canny upper
    circles = cv2.HoughCircles(
        edges,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=image_h * min_dist_ratio,
        param1=param1,
        param2=param2,
        minRadius=int(image_w * min_radius_ratio),
        maxRadius=int(image_w * max_radius_ratio),
    )
    # ... rest same
```

- [ ] **Step 2: Update `find_gauge_center` to pass parameters**
Update the main entry point to accept and forward the new parameters.

- [ ] **Step 3: Run existing tests to ensure no regressions**
Run: `pytest edge/tests/test_find_gauge_center.py`
Expected: PASS

- [ ] **Step 4: Commit engine changes**
```bash
git add edge/gauge_reader/find_gauge_center.py
git commit -m "feat(edge): make circle detection parameters dynamic in engine"
```

### Task 2: Update API and Config

**Files:**
- Modify: `edge/app/api.py`

- [ ] **Step 1: Update `load_config` defaults**
Add the 7 new `circle_*` keys to the `defaults` dictionary in `load_config()`.

- [ ] **Step 2: Update `update_config` and `set_stream_detect_config` allowed keys**
Add the new keys to the `allowed` sets in both endpoints.

- [ ] **Step 3: Update `_run_detection` to pull and pass new params**
Extract the new params from the `cfg` dict and pass them to `find_gauge_center`.

- [ ] **Step 4: Commit API changes**
```bash
git add edge/app/api.py
git commit -m "feat(edge): expose circle detection parameters in API and config"
```

### Task 3: Update UI (Sidebar & Guide)

**Files:**
- Modify: `edge/app/static/index.html`

- [ ] **Step 1: Add "Circle Tuning" card**
Add a new MD3 card before the "Detection" card with inputs for all 7 parameters.

- [ ] **Step 2: Update Tuning Guide**
Add the "Circle detection failure" section to the guide with the tips from the design spec.

- [ ] **Step 3: Update JavaScript helpers**
Update `getFormValues`, `loadConfig`, and `startStreamDetection` to include the new field IDs.

- [ ] **Step 4: Commit UI changes**
```bash
git add edge/app/static/index.html
git commit -m "feat(ui): add circle tuning controls and documentation"
```

### Task 4: End-to-End Verification

- [ ] **Step 1: Verify persistence**
Change a value in the UI (e.g., `Circle Sensitivity` to 40), click "Save", and verify `edge/config.json` contains the updated value.

- [ ] **Step 2: Verify live effect**
Open the "Binary + Ann" stream view. Adjust `Hough Param 2` (Sensitivity) to a very high value (e.g., 200) and verify that the gauge center is no longer detected (HUD should show "No gauge center"). Reset to 50 and verify it returns.

- [ ] **Step 3: Final Commit**
```bash
git commit --allow-empty -m "docs: finalized adjustable circle detection implementation"
```
