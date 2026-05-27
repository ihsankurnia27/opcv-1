# Edge Gauge Detection Pipeline & Web UI Overhaul

## TL;DR

> **Core Objective**: Implement a template/preset system for gauge parameter sets with slider-based UI controls, plus targeted pipeline improvements (CLAHE exposure, confidence rejection, ROI cropping, enhanced Kalman) — all backward compatible.
>
> **Deliverables**:
> - Preset system: CRUD API + config.json schema + management UI panel
> - Slider-based parameter controls replacing raw number inputs
> - Exposed CLAHE clip/tile config, confidence rejection, ROI cropping, 2D Kalman
> - Refactored shared detection library used by both api.py and push_readings.py
> - Export/import presets, parameter reset per section, debounced live tuning
> - TDD test suite for all new code
>
> **Estimated Effort**: Large (15 tasks across 3 waves)
> **Parallel Execution**: YES — 5 waves of 4-6 parallel tasks each
> **Critical Path**: Task 1 → (Tasks 6,7,11) → Task 15 → F1-F4 → user okay

---

## Context

### Original Request
"Analyze the edge/ gauge detection pipeline and how to improve it, and also analyze its web UI, improve the parameters setting by adding templates for presets & sliders for parameters instead of manual input."

### Interview Summary
**Key Decisions**:
- Preset storage: Server-side in edge's config.json (persistent, cross-browser)
- Slider ranges: Smart per-parameter predefined ranges, single JS source of truth
- Scope: Full overhaul — UI + pipeline improvements + enhanced Kalman + config
- Test strategy: TDD (RED-GREEN-REFACTOR) + Agent QA scenarios
- Confidence metric: Combined radial trough + line agreement + vote consensus (0-1)
- ROI cropping: After center detection, 1.5x radius, off by default
- Kalman angle wrap: Cumulative angle unwrapping before update
- CLAHE params: `clahe_clip` + `clahe_tile` exposed for main pipeline
- Web UI: Keep single HTML file, use internal JS module pattern
- push_readings.py: Refactor shared detection logic first, then port

**Metis Review — Identified Gaps Resolved**:
- push_readings.py duplication → refactoring task added as Wave-1 dependency
- Confidence metric definition → combined score formula specified
- Angle wrap in 2D Kalman → cumulative unwrapping technique specified
- Slider range source of truth → single JS object in HTML, documented in plan
- Config backward compat → load_config() defaults.update() handles gracefully

---

## Work Objectives

### Core Objective
Implement a template/preset system for gauge parameter sets with slider-based UI controls, plus targeted pipeline improvements (CLAHE exposure, confidence rejection, ROI cropping, enhanced Kalman) — all backward compatible. The primary deliverable is the preset+slider UX overhaul; pipeline improvements are secondary but scoped in.

### Concrete Deliverables
- Preset CRUD API (`GET/POST/PUT/DELETE /api/presets`, `POST /api/presets/:id/apply`)
- Preset management UI (list, save current, load, delete presets)
- Slider controls for all numeric parameters with smart ranges
- CLAHE clip/tile exposed in config and UI
- Confidence rejection flag in detection output
- Optional ROI cropping after center detection
- Enhanced 2D Kalman filter with cumulative angle unwrapping
- Shared detection library refactored from api.py to gauge_reader/
- push_readings.py ported to shared library
- Parameter reset per config section
- Export/import presets as JSON
- Debounced live tuning (slider -> stream-detect-config)

### Definition of Done
- [ ] All 15 implementation tasks complete with passing tests
- [ ] All 4 verification tasks (F1-F4) pass
- [ ] User explicitly confirms: "okay" or "done"

### Must Have
- Existing config.json must parse after upgrade (backward compatible)
- All existing API endpoints must maintain their response shape
- Presets must survive edge device restart (stored in config.json)
- Sliders must show current numeric value (tooltip or label)
- TDD: each task has RED (failing test) → GREEN (minimal impl) → REFACTOR

### Must NOT Have (Guardrails)
- No new detection algorithms (existing methods only)
- No changes to `/detect` external endpoint's form-parameter interface
- No config.json schema breaking changes
- No adaptive/ML-based parameter tuning
- No mobile-responsive redesign
- No multi-gauge simultaneous support changes
- Preset schema versioning must allow forward compatibility

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest framework in edge/tests/)
- **Automated tests**: TDD — each task begins with test(s) that initially fail
- **Framework**: pytest
- **If TDD**: Each task: RED (failing test for new feature) → GREEN (implement) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Backend API**: Bash (curl) — Send requests, assert status + response fields
- **Frontend/UI**: Playwright — Open browser, interact with sliders/presets, assert DOM
- **Library/Module**: Bash (pytest) — Run tests, assert pass/fail
- **Detection Pipeline**: Bash (python CLI) — Run detection on test images, assert output fields

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — start immediately):
├── Task 1: Refactor shared detection logic to gauge_reader/ library [deep]
├── Task 2: Expose CLAHE clip/tile to config + wire through preprocess [quick]
├── Task 3: Enhanced 2D Kalman + cumulative angle unwrapping [deep]
├── Task 4: Define slider range schema + field metadata [quick]
├── Task 5: Backend preset CRUD API + config extension [unspecified-high]
└── (5 parallel tasks)

Wave 2 (Pipeline features + Frontend — after Wave 1):
├── Task 6: Confidence-based rejection in detection output [deep]
├── Task 7: Optional ROI cropping after center detection [unspecified-high]
├── Task 8: Preset management UI panel [visual-engineering]
├── Task 9: Slider controls replacing number inputs [visual-engineering]
├── Task 10: Parameter reset per section [quick]
├── Task 11: Port push_readings.py to shared detection library [deep]
└── (6 parallel tasks)

Wave 3 (Polish + Integration — after Wave 2):
├── Task 12: Export/import presets (frontend + backend) [unspecified-high]
├── Task 13: Debounced live tuning slider -> stream [quick]
├── Task 14: Update tests for all new features [quick]
├── Task 15: Integration test: backward compat + preset round-trip [deep]
└── (4 parallel tasks)

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high + playwright)
├── Task F4: Scope fidelity check (deep)
└── → Present results → Get explicit user okay

Critical Path: Task 1 → Tasks 6,7,11 → Task 15 → F1-F4 → user okay
Parallel Speedup: ~60% faster than sequential (5 concurrent peak)
Max Concurrent: 6 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 6, 7, 11 |
| 2 | — | — |
| 3 | — | — |
| 4 | — | 8, 9, 10, 13 |
| 5 | — | 8, 12 |
| 6 | 1 | 14, 15 |
| 7 | 1 | 14, 15 |
| 8 | 4, 5 | 12, 14, 15 |
| 9 | 4 | 10, 13, 14, 15 |
| 10 | 9 | 14, 15 |
| 11 | 1 | 14, 15 |
| 12 | 5, 8 | 14, 15 |
| 13 | 9 | 14, 15 |
| 14 | 6, 7, 8, 9, 10, 11, 12, 13 | 15 |
| 15 | 14, 2, 3 | F1-F4 |
| F1 | 1-15 | user okay |
| F2 | 1-15 | user okay |
| F3 | 1-15 | user okay |
| F4 | 1-15 | user okay |

### Agent Dispatch Summary

- **Wave 1**: T1 → `deep`, T2 → `quick`, T3 → `deep`, T4 → `quick`, T5 → `unspecified-high`
- **Wave 2**: T6 → `deep`, T7 → `unspecified-high`, T8 → `visual-engineering`, T9 → `visual-engineering`, T10 → `quick`, T11 → `deep`
- **Wave 3**: T12 → `unspecified-high`, T13 → `quick`, T14 → `quick`, T15 → `deep`
- **FINAL**: F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high` (+ `playwright`), F4 → `deep`

---

## TODOs

- [x] 1. Refactor shared detection logic to gauge_reader/ library

  **What to do**:
  - Extract `_run_detection()`, `_resize_for_detect()`, `_finalize_detect_result()` from `app/api.py` into a new module `gauge_reader/detector.py`
  - Create a `GaugeDetector` class that accepts config dict and exposes `detect(frame) -> dict`
  - Import and use `GaugeDetector` in api.py (minimal change — just swap inline calls)
  - Ensure all imports, coordinate upscaling, debug image generation behave identically
  - The class must accept config overrides (for stream-detect-config flow)
  - Write TDD tests: test that GaugeDetector produces same output as current inline code for 3 test images

  **Must NOT do**:
  - No behavior changes — this is pure structural refactoring
  - Do not change the return format of detection results
  - Do not remove existing `_run_detection()` function until push_readings.py is ported (Task 11)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Requires careful analysis of all call sites to ensure refactoring preserves exact behavior
  - **Skills**: N/A (pure Python refactoring)
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: 6, 7, 11
  - **Blocked By**: None (can start immediately)

  **References**:
  - `app/api.py:473-626` — `_run_detection()` the main detection function to extract
  - `app/api.py:465-470` — `_resize_for_detect()` helper
  - `app/api.py:629-655` — `_finalize_detect_result()` helper
  - `app/api.py:296-351` — stream detect loop that calls `_run_detection()`
  - `push_readings.py:detect_gauge()` — target consumer of the shared library
  - `gauge_reader/__init__.py:1-12` — existing exports pattern to follow
  - Tests in `edge/tests/test_integration.py` — verify same output after refactor

  **Acceptance Criteria**:
  - [ ] `gauge_reader/detector.py` exists with `GaugeDetector` class
  - [ ] `app/api.py` imports and uses `GaugeDetector` instead of inline `_run_detection()`
  - [ ] `pytest edge/tests/ -v` passes (same behavior preserved)
  - [ ] Detection output for 3 test images matches byte-for-byte before refactor

  **QA Scenarios**:
  ```
  Scenario: GaugeDetector produces same result as old inline code
    Tool: Bash (pytest)
    Preconditions: Test images exist in edge/tests/fixtures/
    Steps:
      1. Run `pytest edge/tests/test_detector.py -v`
      2. Assert all tests pass
    Expected Result: Tests pass — GaugeDetector output matches reference output
    Evidence: .omo/evidence/task-1-refactor-tests.txt

  Scenario: api.py still detects correctly via stream
    Tool: Bash (curl)
    Preconditions: Edge API is running, stream is active
    Steps:
      1. `curl -s http://localhost:8765/api/stream-status`
      2. Assert JSON has "value" field (not null)
    Expected Result: Detection works — value field is a number
    Evidence: .omo/evidence/task-1-api-smoke.txt
  ```

- [x] 2. Expose CLAHE clip/tile to config + wire through preprocess pipeline

  **What to do**:
  - Add `clahe_clip` (float, default 2.0) and `clahe_tile` (int, default 8) to `load_config()` defaults
  - Add both keys to `allowed` sets in `update_config()` (line 812-828) and `set_stream_detect_config()` (line 426-437)
  - Modify `gauge_reader/preprocess.py:preprocess()` to accept `clahe_clip` and `clahe_tile` params
  - Modify `_run_detection()` in api.py to pass these config values to `preprocess()`
  - Add both fields as slider inputs in the Detection card of index.html
  - TDD: test that preprocess() with different clip/tile values produces different outputs

  **Must NOT do**:
  - Do not change the existing `circle_clahe_clip` — it's for circle detection only
  - Do not remove the hardcoded defaults from `apply_clahe()` (they become fallbacks)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Well-scoped, touches well-understood code paths
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: None
  - **Blocked By**: None (can start immediately)

  **References**:
  - `gauge_reader/preprocess.py:13-16` — `apply_clahe()` accepts clip/tile
  - `gauge_reader/preprocess.py:41-54` — `preprocess()` currently hardcodes CLAHE params
  - `app/api.py:53-103` — `load_config()` defaults
  - `app/api.py:488-496` — `_run_detection()` preprocess call site
  - `app/api.py:809-834` — `update_config()` allowed keys

  **Acceptance Criteria**:
  - [ ] `config.json` contains `clahe_clip` and `clahe_tile` after save
  - [ ] Changing `clahe_clip` in UI changes actual CLAHE processing (verified via debug image)
  - [ ] `pytest edge/tests/test_preprocess.py -v` passes with new tests

  **QA Scenarios**:
  ```
  Scenario: CLAHE params persist in config
    Tool: Bash (curl)
    Preconditions: Edge API running
    Steps:
      1. `curl -s -X POST -H "Content-Type: application/json" -d '{"clahe_clip":3.0}' http://localhost:8765/api/config`
      2. `curl -s http://localhost:8765/api/config | jq '.clahe_clip'`
      3. Assert value is 3.0
    Expected Result: clahe_clip = 3.0 in config response
    Evidence: .omo/evidence/task-2-config.txt

  Scenario: CLAHE params affect preprocessing output
    Tool: Bash (python)
    Preconditions: Test image available
    Steps:
      1. `python3 -c "import cv2; from gauge_reader.preprocess import preprocess; img=cv2.imread('test.jpg'); r1=preprocess(img, clahe=True, clahe_clip=1.0); r2=preprocess(img, clahe=True, clahe_clip=5.0); print('different:', not (r1==r2).all())"`
      2. Assert output is "different: True"
    Expected Result: Different clip values produce different preprocessed images
    Evidence: .omo/evidence/task-2-preprocess.txt
  ```

- [x] 3. Enhanced 2D Kalman filter with cumulative angle unwrapping

  **What to do**:
  - Extend `gauge_reader/temporal.py:AngleKalman` from 1D (angle only) to 2D (angle + angular velocity)
  - State vector: `[angle, angular_velocity]`
  - Transition model: `angle = angle + dt * angular_velocity`, `angular_velocity = angular_velocity` (constant velocity)
  - Add cumulative angle unwrapping: track unwrapped angle internally, convert back to [0,360) for output
  - Add `angle_kalman_dt` config key (float, default 0.2) for the time step
  - Wire through `_reinit_temporal()` in api.py
  - TDD: test Kalman tracks constant velocity + angle unwrapping across 0/360 boundary

  **Must NOT do**:
  - No adaptive noise or gating (Mahalanobis distance) — scope creep
  - Keep backward compat: existing `R` and `Q` config keys still work

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Requires correct implementation of 2D Kalman math + angle unwrapping edge case
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5)
  - **Blocks**: None
  - **Blocked By**: None (can start immediately)

  **References**:
  - `gauge_reader/temporal.py:38-72` — Existing 1D AngleKalman
  - `app/api.py:133-135` — AngleKalman initialization
  - `app/api.py:148-150` — `_reinit_temporal()` wiring
  - `app/api.py:568-571` — Kalman update in detection pipeline

  **Acceptance Criteria**:
  - [ ] `AngleKalman` has 2D state `[angle, vel]` and handles angle unwrapping
  - [ ] 355° → 5° produces a small (+10°) update, not large (-350°) update
  - [ ] `pytest edge/tests/test_temporal.py -v` passes with new tests

  **QA Scenarios**:
  ```
  Scenario: Kalman handles 0/360 wrap-around correctly
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. `python3 -c "from gauge_reader.temporal import AngleKalman; k=AngleKalman(); k.update(355); result=k.update(5); print('result:', round(result,1))"`
      2. Assert result is close to ~357 (not ~180)
    Expected Result: Kalman smoothly tracks across the boundary
    Evidence: .omo/evidence/task-3-kalman-wrap.txt

  Scenario: Kalman smooths noisy measurements
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run test `pytest edge/tests/test_temporal.py::test_enhanced_kalman_smoothing -v`
      2. Assert test passes
    Expected Result: Kalman output variance < measurement variance
    Evidence: .omo/evidence/task-3-kalman-smooth.txt
  ```

- [x] 4. Define slider range schema + field metadata

  **What to do**:
  - In the `<script>` section of `index.html`, create a `SLIDER_RANGES` constant object defining min, max, step for every numeric config parameter
  - For odd-only params (blur_kernel, threshold_block): step=2, ensure min/max are odd
  - For boolean params (use_clahe, circle_adaptive_thresh, cam_auto_exposure): exclude from sliders (remain checkboxes)
  - For select params (detect_method, cam_resolution, point, stream_mode, etc.): exclude from sliders (remain selects)
  - For text params (server_api_url, api_key): exclude from sliders
  - Document all slider ranges below in this task's What to do
  - TDD test: verify SLIDER_RANGES covers all numeric config keys from `getFormValues()` except excluded types

  **Slider Range Reference** (all ranges):

  | Parameter | Min | Max | Step | Notes |
  |-----------|-----|-----|------|-------|
  | min_value | -99999 | 99999 | 0.1 | No practical bound |
  | max_value | -99999 | 99999 | 0.1 | No practical bound |
  | min_angle | 0 | 360 | 1 | Degrees |
  | max_angle | 0 | 360 | 1 | Degrees |
  | center_offset_y | -200 | 200 | 1 | Pixels |
  | inner_ratio | 0.1 | 0.95 | 0.05 | Fraction of radius |
  | outer_ratio | 0.15 | 1.0 | 0.05 | Fraction of radius |
  | blur_kernel | 1 | 31 | 2 | Odd only |
  | threshold_block | 0 | 99 | 2 | 0=off, odd only |
  | threshold_c | 0 | 20 | 1 | Constant |
  | circle_hough_param1 | 50 | 300 | 5 | Canny threshold |
  | circle_hough_param2 | 10 | 150 | 5 | Accumulator threshold |
  | circle_hough_dp | 0.5 | 3.0 | 0.1 | Inverse ratio |
  | circle_canny_low | 10 | 300 | 5 | Low threshold |
  | circle_canny_high | 20 | 500 | 5 | High threshold |
  | circle_dilate | 0 | 10 | 1 | Iterations |
  | circle_clahe_clip | 0.5 | 10.0 | 0.5 | Clip limit |
  | clahe_clip | 0.5 | 10.0 | 0.5 | Main pipeline CLAHE |
  | clahe_tile | 2 | 16 | 2 | Tile grid size |
  | circle_min_circularity | 0.1 | 1.0 | 0.05 | Shape threshold |
  | circle_min_dist_ratio | 0.1 | 1.0 | 0.05 | Fraction |
  | circle_min_radius_ratio | 0.01 | 0.4 | 0.05 | Fraction of width |
  | circle_max_radius_ratio | 0.1 | 0.7 | 0.05 | Fraction of width |
  | filter_alpha | 0.01 | 0.95 | 0.05 | EMA rate |
  | filter_max_jump | 0.1 | 10.0 | 0.5 | Spike threshold |
  | filter_window | 1 | 21 | 2 | Median window |
  | center_ema | 0.05 | 0.95 | 0.05 | Center tracking |
  | angle_kalman_R | 0.01 | 5.0 | 0.05 | Measurement noise |
  | angle_kalman_Q | 0.001 | 1.0 | 0.005 | Process noise |
  | angle_kalman_dt | 0.05 | 1.0 | 0.05 | Time step |
  | interval_seconds | 30 | 86400 | 30 | 30s to 24h |
  | cam_brightness | -1 | 255 | 1 | -1=default |
  | cam_contrast | -1 | 255 | 1 | -1=default |
  | cam_gain | -1 | 255 | 1 | -1=default |
  | cam_exposure_absolute | -1 | 10000 | 10 | -1=default |

  **Must NOT do**:
  - Do NOT apply sliders yet — this task only defines the schema
  - Do NOT remove existing number inputs (Task 9 does the replacement)
  - Do NOT send ranges to the backend — they are purely frontend concern

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure data definition, no complex logic
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: 8, 9, 10, 13
  - **Blocked By**: None (can start immediately)

  **References**:
  - `index.html:1595-1612` — `getFormValues()` lists all config fields
  - `index.html:1434-1448` — `startStreamDetection()` sends config fields
  - The table above (all slider ranges)

  **Acceptance Criteria**:
  - [ ] `SLIDER_RANGES` constant defined in index.html `<script>` section
  - [ ] Every numeric config key in `getFormValues()` has an entry in `SLIDER_RANGES`
  - [ ] Checkboxes, selects, text inputs are excluded
  - [ ] `pytest` test verifies complete coverage

  **QA Scenarios**:
  ```
  Scenario: SLIDER_RANGES covers all numeric config keys
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run `pytest edge/tests/test_slider_ranges.py -v`
      2. Assert test passes
    Expected Result: Test verifies complete coverage of numeric params
    Evidence: .omo/evidence/task-4-coverage.txt
  ```

- [x] 5. Backend preset CRUD API + config extension

  **What to do**:
  - Add `presets` key to config.json schema: `presets: [{"id": string, "name": string, "params": {key: value}, "created": timestamp}]`
  - Create endpoints in `app/api.py`:
    - `GET /api/presets` → return list of all presets
    - `POST /api/presets` → create new preset (body: `{name, params}`), auto-generate UUID id, return 201
    - `GET /api/presets/{id}` → return single preset
    - `PUT /api/presets/{id}` → update preset
    - `DELETE /api/presets/{id}` → delete, return 204
    - `POST /api/presets/{id}/apply` → load preset params into `_detect_config` (NOT config.json)
  - Generate UUID for preset IDs via `uuid.uuid4().hex[:12]`
  - On duplicate name: overwrite silently (last-write-wins)
  - Validate applied preset: unknown keys are silently ignored, missing keys use current config defaults
  - TDD: test full CRUD cycle (create, read, update, delete, apply)

  **Must NOT do**:
  - No preset versioning or migration system
  - No preset sharing between edge devices
  - No preset search/filter

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multiple endpoints, config.json file I/O, error handling
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4)
  - **Blocks**: 8, 12
  - **Blocked By**: None (can start immediately)

  **References**:
  - `app/api.py:53-103` — `load_config()` pattern to follow
  - `app/api.py:106-108` — `save_config()` pattern for writing config.json
  - `app/api.py:425-446` — `set_stream_detect_config()` pattern for loading into _detect_config
  - `app/api.py:809-835` — `update_config()` allowed keys pattern
  - `app/api.py:802-806` — `get_config()` return pattern

  **Acceptance Criteria**:
  - [ ] `POST /api/presets` returns 201 with `{id, name, params, created}`
  - [ ] `GET /api/presets` returns array
  - [ ] `PUT /api/presets/{id}` updates existing preset
  - [ ] `DELETE /api/presets/{id}` returns 204
  - [ ] `POST /api/presets/{id}/apply` loads params into detection config
  - [ ] `pytest edge/tests/test_presets.py -v` passes

  **QA Scenarios**:
  ```
  Scenario: Full preset CRUD cycle
    Tool: Bash (curl)
    Preconditions: Edge API running
    Steps:
      1. CREATE: `curl -s -X POST -H "Content-Type: application/json" -d '{"name":"daylight","params":{"blur_kernel":7,"threshold_block":11}}' http://localhost:8765/api/presets`
      2. Assert 201, capture id
      3. LIST: `curl -s http://localhost:8765/api/presets | jq 'length'`
      4. Assert > 0
      5. APPLY: `curl -s -X POST http://localhost:8765/api/presets/$id/apply | jq '.ok'`
      6. Assert true
      7. DELETE: `curl -s -o /dev/null -w '%{http_code}' -X DELETE http://localhost:8765/api/presets/$id`
      8. Assert 204
    Expected Result: Full CRUD cycle works
    Evidence: .omo/evidence/task-5-crud.txt

  Scenario: Apply unknown keys silently ignores them
    Tool: Bash (curl)
    Preconditions: Edge API running
    Steps:
      1. CREATE: `curl -s -X POST -H "Content-Type: application/json" -d '{"name":"test","params":{"nonexistent_key":999}}' http://localhost:8765/api/presets`
      2. Capture id from response
      3. APPLY: `curl -s -X POST http://localhost:8765/api/presets/$id/apply | jq '.ok'`
      4. Assert true
    Expected Result: Unknown keys don't crash the apply
    Evidence: .omo/evidence/task-5-unknown-keys.txt
  ```

- [x] 6. Confidence-based rejection in detection output

  **What to do**:
  - Add `"confidence": float` field to detection result dict in `_run_detection()` (api.py:616-626)
  - Confidence formula: `(radial_trough_sharpness + line_confidence + strategy_consensus) / 3.0`
    - radial_trough_sharpness: how much darker the minimum ray is vs median (from `_needle_radial_angle`)
    - line_confidence: from `_needle_line_angle()` return value
    - strategy_consensus: 1.0 if majority of strategies agree within 5°, 0.5 if partial, 0.0 if only one strategy
  - Add `min_confidence: float` (default 0.0) to config — 0.0 means never reject
  - When `confidence < min_confidence` AND `min_confidence > 0`: set `"rejected": true` in result, keep value but flag it
  - Stream HUD: show confidence value (yellow if low, red if rejected)
  - TDD: test confidence values for known-good and known-bad images
  - Extract `_needle_radial_angle` confidence logic from `find_needle.py` into a reusable function

  **Must NOT do**:
  - Never return error instead of value — rejected detections still have value + `"rejected": true`
  - Do not change detection output shape for external consumers — confidence is additive

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Requires understanding all three needle detection strategies to compute meaningful confidence
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 11)
  - **Blocks**: 14, 15
  - **Blocked By**: 1

  **References**:
  - `gauge_reader/find_needle.py:75-119` — `_needle_radial_angle()` already computes confidence (line 112-117)
  - `gauge_reader/find_needle.py:13-72` — `_needle_line_angle()` returns confidence (line 69-71)
  - `gauge_reader/find_needle.py:143-189` — `_vote_angles()` has agreement logic usable for strategy_consensus
  - `app/api.py:616-626` — detection result dict where confidence will be added
  - `app/api.py:296-351` — stream loop that renders detection results

  **Acceptance Criteria**:
  - [ ] Detection output includes `"confidence": float` (0-1)
  - [ ] Config includes `min_confidence: float` (default 0.0)
  - [ ] When confidence < min_confidence: result has `"rejected": true`
  - [ ] `pytest edge/tests/test_confidence.py -v` passes

  **QA Scenarios**:
  ```
  Scenario: Detection result includes confidence
    Tool: Bash (curl)
    Preconditions: Edge API running, stream active
    Steps:
      1. `curl -s http://localhost:8765/api/stream-status | jq '.confidence'`
      2. Assert confidence is a number between 0 and 1
    Expected Result: confidence field present and in range
    Evidence: .omo/evidence/task-6-confidence.txt

  Scenario: Low confidence detection shows rejected flag
    Tool: Bash (curl)
    Preconditions: Edge API running, stream active
    Steps:
      1. Set min_confidence: `curl -s -X POST -H "Content-Type: application/json" -d '{"min_confidence":0.9}' http://localhost:8765/api/stream-detect-config`
      2. Poll stream-status: `curl -s http://localhost:8765/api/stream-status | jq '.rejected'`
      3. If true: test passes (confidence is realistically below 0.9 most of the time)
    Expected Result: rejected field is true or false
    Evidence: .omo/evidence/task-6-rejected.txt
  ```

- [x] 7. Optional ROI cropping after center detection

  **What to do**:
  - Add `use_roi: bool` (default false) and `roi_margin: float` (default 1.5) to config
  - In `_run_detection()`: after center is found and BEFORE needle detection, if `use_roi`:
    - Crop frame to `[cx - radius*roi_margin : cx + radius*roi_margin, cy - radius*roi_margin : cy + radius*roi_margin]`
    - Update cx, cy, radius relative to the cropped region
    - Run needle detection on cropped frame
    - Upscale needle coordinates back to original frame after detection
  - Ensure this is off by default to not break existing setups
  - Wire `use_roi` and `roi_margin` through config and UI
  - TDD: test ROI cropping produces same needle angle as full-frame for centered gauges

  **Must NOT do**:
  - No adaptive ROI (user must opt in)
  - No ROI cropping before center detection (that would be manual ROI, different feature)
  - No cv2.UMat optimization (beyond scope — simple numpy slicing is fine for Orange Pi)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Coordinate transformations require careful handling; moderate complexity
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 8, 9, 10, 11)
  - **Blocks**: 14, 15
  - **Blocked By**: 1

  **References**:
  - `app/api.py:473-626` — `_run_detection()` where ROI insertion happens
  - `app/api.py:573-577` — coordinate upscaling logic (must adapt for ROI offset)
  - `app/api.py:53-103` — `load_config()` defaults
  - `app/api.py:812-828` — allowed keys update

  **Acceptance Criteria**:
  - [ ] `use_roi` and `roi_margin` in config (defaults: false, 1.5)
  - [ ] When `use_roi=true`: needle detection runs on cropped region, coordinates correct
  - [ ] When `use_roi=false`: behavior identical to current (no change)
  - [ ] `pytest edge/tests/test_roi.py -v` passes

  **QA Scenarios**:
  ```
  Scenario: ROI off by default — no behavior change
    Tool: Bash (curl)
    Preconditions: Edge API running, stream active
    Steps:
      1. `curl -s http://localhost:8765/api/config | jq '{use_roi, roi_margin}'`
      2. Assert use_roi is false
    Expected Result: use_roi=false, roi_margin=1.5 by default
    Evidence: .omo/evidence/task-7-defaults.txt

  Scenario: ROI cropping produces same angle as full frame
    Tool: Bash (python)
    Preconditions: Test image with centered gauge
    Steps:
      1. Run `pytest edge/tests/test_roi.py::test_roi_matches_full_frame -v`
      2. Assert test passes
    Expected Result: ROI cropped detection matches full-frame within tolerance
    Evidence: .omo/evidence/task-7-roi-match.txt
  ```

- [x] 8. Preset management UI panel

  **What to do**:
  - Add a new config card "Presets" in index.html (between Detection and Smoothing cards)
  - Panel contains:
    - Dropdown `<select>` listing all presets by name
    - "Load" button → calls `POST /api/presets/{id}/apply`, updates slider values in UI
    - "Save Current" button → opens inline prompt for name, calls `POST /api/presets`
    - "Delete" button → confirms then calls `DELETE /api/presets/{id}`
    - "Refresh" button → re-fetches preset list
  - On load: populate dropdown from `GET /api/presets`
  - On preset select in dropdown: show preview of params (number of params, created date)
  - Wire "Save Current" to grab current slider values from `getFormValues()`
  - After "Load": call `refreshSliders()` to update slider positions
  - Handle empty state: "No presets saved yet" message
  - Handle error state: toast on API failure
  - TDD: test client-side preset rendering (Playwright)

  **Must NOT do**:
  - No drag-to-reorder, no search, no favorites, no tags
  - No tabs or categories

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: New UI component requires layout, styling, and interaction logic
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 9, 10, 11)
  - **Blocks**: 12, 14, 15
  - **Blocked By**: 4, 5

  **References**:
  - `index.html:850-903` — existing config card pattern (Calibration card)
  - `index.html:1594-1656` — `getFormValues()` and `loadConfig()` patterns
  - `index.html:1070-1078` — `api()` helper for API calls
  - `index.html:1081-1090` — `toast()` for notifications

  **Acceptance Criteria**:
  - [ ] "Presets" card exists in config column
  - [ ] Dropdown shows presets from API
  - [ ] "Load" applies preset and updates sliders
  - [ ] "Save Current" creates new preset from current slider values
  - [ ] "Delete" removes preset
  - [ ] Empty state shows "No presets saved yet"

  **QA Scenarios**:
  ```
  Scenario: Create and load a preset via UI
    Tool: Playwright
    Preconditions: Edge API running, browser open to UI
    Steps:
      1. Click "Save Current" in Presets card
      2. Type "test-preset" in prompt
      3. Confirm
      4. Select "test-preset" from dropdown
      5. Click "Load"
      6. Observe slider values update
    Expected Result: Preset is saved and loaded, sliders update
    Evidence: .omo/evidence/task-8-preset-ui.png

  Scenario: Preset card shows empty state
    Tool: Playwright
    Preconditions: No presets exist
    Steps:
      1. Open UI page
      2. Look at Presets card
      3. Assert "No presets saved yet" visible
    Expected Result: Empty state message displayed
    Evidence: .omo/evidence/task-8-empty.png
  ```

- [x] 9. Slider controls replacing number inputs

  **What to do**:
  - Refactor each numeric `<input type="number">` in index.html to use `<input type="range">` with values from `SLIDER_RANGES`
  - Each slider must show its current value as a `<span>` next to the slider (or inside a tooltip)
  - Add a `refreshSliders()` JS function that reads values from the input elements and updates slider positions + value labels
  - Slider min/max/step come from `SLIDER_RANGES[fieldName]`
  - Debounce slider onChange by 300ms before updating `_detect_config` (to avoid 40 POSTs per second)
  - Ensure sliders update the underlying `<input>` values so `getFormValues()` still works unchanged
  - Keep existing `<input type="number">` hidden alongside sliders for JS compatibility
  - Style sliders to match MD3 theme (teal/cyan accent color)
  - Add CSS for range inputs: custom thumb, track, focus states
  - Keep checkboxes (use_clahe, circle_adaptive_thresh, cam_auto_exposure) unchanged
  - Keep select dropdowns (detect_method, cam_resolution, point, stream_mode, stream_fps, stream_quality) unchanged
  - TDD: Playwright test that slider moves and value updates

  **Must NOT do**:
  - Do not remove `getFormValues()` compatibility — it must still return correct values
  - Do not convert checkboxes or selects to sliders
  - Do not change the Save/Load config logic

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 30+ slider components with MD3 styling, requires careful CSS + JS
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8, 10, 11)
  - **Blocks**: 10, 13, 14, 15
  - **Blocked By**: 4

  **References**:
  - `index.html:295-371` — existing input/select CSS styles
  - `index.html:1594-1612` — `getFormValues()` — must remain compatible
  - `index.html:1434-1448` — `startStreamDetection()` — reads form values
  - `index.html:169-232` — existing button/card CSS patterns
  - `SLIDER_RANGES` constant from Task 4

  **Acceptance Criteria**:
  - [ ] All numeric params use `<input type="range">` with value labels
  - [ ] `getFormValues()` returns same values as before (tested)
  - [ ] Checkboxes and selects remain unchanged
  - [ ] Slider thumb and track styled with MD3 teal accent
  - [ ] Slider onChange debounced at 300ms
  - [ ] `pytest` + Playwright test passes

  **QA Scenarios**:
  ```
  Scenario: Slider moves and updates value
    Tool: Playwright
    Preconditions: Browser open to UI
    Steps:
      1. Locate blur_kernel slider
      2. Drag slider to value 11
      3. Assert value label shows "11"
      4. Assert hidden input value is "11"
      5. Call getFormValues() — assert blur_kernel = 11
    Expected Result: Slider updates both display and underlying value
    Evidence: .omo/evidence/task-9-slider-move.png

  Scenario: Checkboxes remain unchanged
    Tool: Playwright
    Preconditions: Browser open to UI
    Steps:
      1. Locate use_clahe checkbox
      2. Assert it's an input[type="checkbox"], not a range
    Expected Result: Checkboxes still use checkbox input type
    Evidence: .omo/evidence/task-9-checkbox.png
  ```

- [ ] 10. Parameter reset per section

  **What to do**:
  - Add a small "Reset" button (btn-xs, outlined) to the top-right of each config card
  - On click: reset all sliders/inputs in that card to the values from the last-saved config.json
  - Store saved config snapshot in a JS variable `lastSavedConfig` (populated after `loadConfig()` and `saveConfig()`)
  - For cards that span multiple parameter groups, only reset the params belonging to that card
  - Define a `CARD_FIELDS` mapping: which field IDs belong to which card
  - After reset, call `refreshSliders()` to update slider positions
  - TDD: Playwright test that reset restores saved values

  **Must NOT do**:
  - No "Reset All to Factory" — only per-section reset to last-saved config
  - No auto-save after reset

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Well-scoped feature reusing existing patterns
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8, 9, 11)
  - **Blocks**: 14, 15
  - **Blocked By**: 9

  **References**:
  - `index.html:1614-1656` — `loadConfig()` pattern for reading saved config
  - `index.html:1947-1953` — `saveConfig()` pattern for updating saved config
  - `index.html:775-960` — config cards with their field IDs

  **Acceptance Criteria**:
  - [ ] "Reset" button visible in each config card
  - [ ] Reset restores saved config.json values
  - [ ] After reset, sliders and value labels update
  - [ ] `lastSavedConfig` populated after load/save

  **QA Scenarios**:
  ```
  Scenario: Reset restores saved values
    Tool: Playwright
    Preconditions: Config loaded, slider values changed
    Steps:
      1. Change blur_kernel slider to 15
      2. Click "Reset" in Detection card
      3. Assert blur_kernel returns to saved value
    Expected Result: Slider resets to saved config value
    Evidence: .omo/evidence/task-10-reset.png
  ```

- [x] 11. Port push_readings.py to shared detection library

  **What to do**:
  - Replace the duplicated detection logic in `push_readings.py:detect_gauge()` with `GaugeDetector` from `gauge_reader/detector.py`
  - The function should: create `GaugeDetector(config)`, call `detect(frame)`, get result
  - Ensure all temporal filtering (CenterTracker, AngleKalman, ValueFilter) — which is also duplicated in push_readings.py — uses the shared instances
  - Verify push_readings.py produces identical readings as before the refactor
  - TDD: integration test comparing push_readings output with api.py detection for same frame

  **Must NOT do**:
  - No behavior changes to push_readings.py scheduling or push logic
  - No changes to push_readings.py CLI interface

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Requires careful comparison of old vs new detection output to ensure identical behavior
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8, 9, 10)
  - **Blocks**: 14, 15
  - **Blocked By**: 1

  **References**:
  - `push_readings.py` — entire file, especially `detect_gauge()` function
  - `gauge_reader/detector.py` — new GaugeDetector from Task 1
  - `app/api.py:132-151` — temporal filter initialization
  - `app/api.py:296-351` — stream detect loop (temporal filter usage pattern)

  **Acceptance Criteria**:
  - [ ] `push_readings.py` uses `GaugeDetector` from shared library
  - [ ] Push readings output matches pre-refactor output (verified by test)
  - [ ] `pytest edge/tests/test_push_readings.py -v` passes
  - [ ] `python3 push_readings.py --dry-run` exits 0

  **QA Scenarios**:
  ```
  Scenario: push_readings uses shared detector
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. Run `pytest edge/tests/test_push_readings.py::test_uses_shared_detector -v`
      2. Assert test passes
    Expected Result: push_readings imports from gauge_reader.detector
    Evidence: .omo/evidence/task-11-shared.txt

  Scenario: push_readings dry-run works
    Tool: Bash (interactive)
    Preconditions: Test image available
    Steps:
      1. `python3 edge/push_readings.py --dry-run --image test.jpg`
      2. Assert exits 0
    Expected Result: Dry-run produces detection output
    Evidence: .omo/evidence/task-11-dry-run.txt
  ```

- [ ] 12. Export/import presets as JSON

  **What to do**:
  - **Export**: Add "Export" button in Presets card → calls `GET /api/presets`, formats as JSON, triggers browser download as `edge-presets-{date}.json`
  - **Import**: Add "Import" button → file picker accepting `.json` → reads file → calls `POST /api/presets/import` (new endpoint) that bulk-creates presets
  - Backend `POST /api/presets/import` endpoint:
    - Accepts `{presets: [{name, params}], version: 1}`
    - On duplicate name: overwrite silently
    - On unknown version: reject with 400
    - Returns `{imported: N, skipped: N}`
  - Export format: `{version: 1, exported_at: timestamp, presets: [{id, name, params, created}]}`
  - Frontend: handle file picker via hidden `<input type="file">` triggered by button click
  - TDD: test import with valid format, invalid format, duplicate names

  **Must NOT do**:
  - No merge logic — import always replaces existing presets with same name
  - No export of current config.json (only presets)
  - No download to server filesystem (browser download only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Backend endpoint + frontend file handling + error handling
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 13, 14, 15)
  - **Blocks**: 14, 15
  - **Blocked By**: 5, 8

  **References**:
  - `app/api.py:106-108` — `save_config()` pattern
  - Task 5 preset CRUD API patterns
  - `index.html:1070-1078` — `api()` helper
  - `index.html:1534-1559` — existing form/upload pattern (sendToServer)

  **Acceptance Criteria**:
  - [ ] "Export" downloads `edge-presets-{date}.json` with all presets
  - [ ] "Import" accepts valid JSON file and creates presets
  - [ ] Import with duplicate names overwrites existing
  - [ ] Import with invalid format shows error toast
  - [ ] `pytest edge/tests/test_preset_import.py -v` passes

  **QA Scenarios**:
  ```
  Scenario: Export presets as JSON
    Tool: Playwright
    Preconditions: At least one preset exists
    Steps:
      1. Click "Export" in Presets card
      2. Assert browser downloads a .json file
      3. Open downloaded file — assert has version, presets array, name field
    Expected Result: JSON file downloaded with correct structure
    Evidence: .omo/evidence/task-12-export.png

  Scenario: Import presets from JSON
    Tool: Playwright + Bash
    Preconditions: export.json from previous scenario
    Steps:
      1. Click "Import" in Presets card
      2. Select export.json
      3. Assert toast shows "imported N presets"
      4. Assert preset dropdown now shows imported presets
    Expected Result: Presets imported and visible in UI
    Evidence: .omo/evidence/task-12-import.png
  ```

- [ ] 13. Debounced live tuning slider -> stream-detect-config

  **What to do**:
  - Create a `debounce(fn, delay)` helper in the JS section of index.html
  - Add an `onSliderChange()` event handler attached to all slider inputs
  - When slider changes: update the value label immediately, debounce the API call to `POST /api/stream-detect-config` by 300ms
  - The debounced call sends only the changed parameter (not all 40 params) to minimize payload
  - If stream is not active (`streamDetectActive == false`), skip the API call entirely
  - Handle race condition: if a new change comes while previous debounce is pending, cancel the old and schedule new
  - TDD: Playwright test slider drag triggers stream-detect-config call

  **Must NOT do**:
  - No API call on slider change when stream is off
  - No removing existing `startStreamDetection()` — this supplements it

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small JS utility with clear behavior
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12, 14, 15)
  - **Blocks**: 14, 15
  - **Blocked By**: 9

  **References**:
  - `index.html:1433-1456` — existing `startStreamDetection()` which sends all params
  - `index.html:425-446` — `POST /api/stream-detect-config` backend endpoint
  - `index.html:1458-1464` — `stopStreamDetection()` pattern

  **Acceptance Criteria**:
  - [ ] `debounce()` helper function exists
  - [ ] Slider change triggers debounced call to `/api/stream-detect-config`
  - [ ] No API call when stream is not active
  - [ ] Rapid slider changes only trigger one API call after 300ms pause

  **QA Scenarios**:
  ```
  Scenario: Slider change triggers debounced stream config update
    Tool: Playwright
    Preconditions: Edge API running, stream detect active
    Steps:
      1. Start stream detect (click "Detect")
      2. Change blur_kernel slider from 5 to 9
      3. Wait 500ms
      4. Assert /api/stream-detect-config was called with blur_kernel=9
    Expected Result: Debounced API call made with new value
    Evidence: .omo/evidence/task-13-debounce.txt

  Scenario: No API call when stream off
    Tool: Playwright
    Preconditions: Edge API running, stream stopped
    Steps:
      1. Ensure stream is stopped
      2. Change blur_kernel slider from 5 to 9
      3. Wait 500ms
      4. Assert no API call to /api/stream-detect-config was made
    Expected Result: No API call when stream not active
    Evidence: .omo/evidence/task-13-no-call.txt
  ```

- [ ] 14. Update tests for all new features

  **What to do**:
  - Ensure all new code has TDD tests (RED phase was already done per task)
  - Add integration tests that exercise multiple features together:
    - Preset save → load → verify slider values updated
    - CLAHE config change → verify preprocessing output changes
    - ROI enable → verify needle angle matches full-frame
    - Confidence rejection → verify rejected flag
    - Export → Import → verify presets round-trip
    - Push readings with shared GaugeDetector → verify output
  - Add edge case tests:
    - Empty preset list
    - Apply preset with unknown keys
    - Kalman with large angle jump (simulating occlusion recovery)
    - ROI with gauge at image edge (partial crop)
    - Confidence with synthetic low-contrast image
  - Ensure all new tests pass: `pytest edge/tests/ -v`
  - Update `edge/tests/__init__.py` if needed for test fixtures

  **Must NOT do**:
  - No changing existing tests that pass (unless they test changed behavior)
  - No testing external UI behavior (that's Playwright in QA scenarios)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Test-focused task with clear scope
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12, 13, 15)
  - **Blocks**: 15
  - **Blocked By**: 6, 7, 8, 9, 10, 11, 12, 13

  **References**:
  - `edge/tests/` — all existing test files (pattern to follow)
  - `edge/tests/test_integration.py` — integration test pattern
  - `edge/tests/test_preprocess.py` — preprocess test pattern
  - `edge/tests/test_temporal.py` — temporal filter test pattern

  **Acceptance Criteria**:
  - [ ] Tests exist for all new features
  - [ ] Integration tests cover cross-feature scenarios
  - [ ] Edge case tests exist (empty, boundary, extreme values)
  - [ ] `pytest edge/tests/ -v` — all tests pass

  **QA Scenarios**:
  ```
  Scenario: All tests pass
    Tool: Bash (pytest)
    Preconditions: Python venv with dependencies
    Steps:
      1. `cd edge && python -m pytest tests/ -v 2>&1`
      2. Assert exit code 0
      3. Assert all tests pass (no FAILED, no ERROR)
    Expected Result: All tests green
    Evidence: .omo/evidence/task-14-all-tests.txt
  ```

- [ ] 15. Integration test: backward compat + preset round-trip

  **What to do**:
  - Create a comprehensive integration test that validates the full upgrade scenario:
    1. Load old-format config.json (without new keys) → verify all new keys get defaults
    2. Save a preset → re-load config → verify preset persists
    3. Export presets → clear presets → import → verify they match
    4. Apply ROI + confidence features → verify detection still works
    5. Run full detection pipeline with all new features enabled → verify output format
  - Create synthetic test images for deterministic results (not camera-dependent)
  - Test that `/api/config` still returns the exact same shape for existing keys
  - Test that `/detect` external endpoint works unchanged
  - TDD: write test first, then implement fixes if any fail

  **Must NOT do**:
  - No hardware-dependent tests (use synthetic images, not camera)
  - No tests that modify actual config.json on production devices

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Comprehensive integration test covering the entire pipeline upgrade scenario
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12, 13, 14)
  - **Blocks**: F1-F4
  - **Blocked By**: 14, 2, 3

  **References**:
  - `edge/tests/test_integration.py` — existing integration test pattern
  - `edge/tests/test_find_needle.py` — needle test with synthetic images
  - `app/api.py:53-103` — `load_config()` defaults (backward compat)
  - `app/api.py:918-969` — `/detect` external endpoint (must be unchanged)

  **Acceptance Criteria**:
  - [ ] Old config.json loads without errors (all new keys get defaults)
  - [ ] Preset save → load → export → import → match
  - [ ] `/detect` endpoint unchanged (same param names, same response shape)
  - [ ] All features enabled: detection still produces valid results
  - [ ] `pytest edge/tests/test_integration.py -v` passes

  **QA Scenarios**:
  ```
  Scenario: Old config loads with defaults for new keys
    Tool: Bash (python)
    Preconditions: Old-format config.json fixture (no clahe_clip, use_roi, etc.)
    Steps:
      1. Run `pytest edge/tests/test_integration.py::test_old_config_loads -v`
      2. Assert test passes — clahe_clip=2.0, use_roi=False, etc.
    Expected Result: New keys get default values from load_config()
    Evidence: .omo/evidence/task-15-old-config.txt

  Scenario: Full preset round-trip
    Tool: Bash (curl + python)
    Preconditions: Edge API running
    Steps:
      1. Create preset: `curl -s -X POST -H "Content-Type: application/json" -d '{"name":"rt-test","params":{"blur_kernel":9}}' http://localhost:8765/api/presets`
      2. Export: `curl -s http://localhost:8765/api/presets > /tmp/export.json`
      3. Delete all presets
      4. Import: `curl -s -X POST -H "Content-Type: application/json" -d @/tmp/export.json http://localhost:8765/api/presets/import`
      5. List: `curl -s http://localhost:8765/api/presets | jq 'length'`
      6. Assert >= 1
    Expected Result: Presets survive export → delete → import round-trip
    Evidence: .omo/evidence/task-15-roundtrip.txt
  ```

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `pytest` + linter. Review all changed files for: `as any`/type ignores, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (preset save→load→apply, slider→stream-detect-config). Test edge cases: empty presets, invalid export files, low-confidence detection. Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1**: `refactor(gauge_reader): extract shared detection logic for push_readings reuse`
- **2**: `feat(config): expose CLAHE clip/tile params for main pipeline`
- **3**: `feat(kalman): enhanced 2D Kalman with angle unwrapping`
- **4**: `feat(ui): define slider range schema for all numeric params`
- **5**: `feat(api): preset CRUD endpoints + config extension`
- **6**: `feat(detect): confidence-based rejection with min_confidence config`
- **7**: `feat(detect): optional ROI cropping after center detection`
- **8**: `feat(ui): preset management panel`
- **9**: `feat(ui): slider controls replacing number inputs`
- **10**: `feat(ui): parameter reset per section`
- **11**: `refactor(push): port to shared detection library`
- **12**: `feat(ui): export/import presets as JSON`
- **13**: `feat(ui): debounced live tuning slider -> stream-detect-config`
- **14**: `test: update test suite for all new features`
- **15**: `test: integration tests for backward compat + preset round-trip`

Pre-commit each task: `pytest` must pass.

---

## Success Criteria

### Verification Commands
```bash
# All tests pass
pytest edge/tests/ -v  # Expected: all tests pass

# API smoke tests
curl -s http://localhost:8765/api/config | jq '.clahe_clip'  # Expected: 2.0
curl -s http://localhost:8765/api/presets | jq 'type'  # Expected: "array"
curl -s -X POST -H "Content-Type: application/json" -d '{"name":"test","params":{}}' http://localhost:8765/api/presets | jq '.name'  # Expected: "test"

# Detection output with confidence
curl -s http://localhost:8765/api/stream-status | jq '.confidence'  # Expected: float or null

# Push readings still works
python3 edge/push_readings.py --dry-run  # Expected: exits 0
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Existing edge device upgrades without manual intervention
- [ ] User confirms: "okay"
