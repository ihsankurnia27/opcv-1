# Edge Pipeline Improvements — Learnings

## Task 1: Refactor detection logic to gauge_reader/detector.py

### Context
- `app/api.py` has ~3 inline detection functions: `_run_detection()`, `_resize_for_detect()`, `_finalize_detect_result()`
- `_run_detection()` is ~150 lines at lines 473-626
- Detection resolution: `_DETECT_USE_W = 480` in api.py
- Config values are all strings in config.json, load_config() converts with float()/int()
- Detection runs at 480px internally, coords upscaled to original resolution
- `push_readings.py` has its own inline detection pipeline (to be refactored in Task 11)

### Dependencies
- gauge_reader/preprocess.py: preprocess()
- gauge_reader/find_gauge_center.py: find_gauge_center(), find_gauge_center_legacy()
- gauge_reader/find_needle.py: find_needle_angle()
- gauge_reader/find_needle_radial.py: find_needle_angle_legacy(), draw_needle()
- gauge_reader/draw.py: draw_needle()
- gauge_reader/temporal.py: CenterTracker, AngleKalman
- gauge_reader/__init__.py: angle_to_value()

### Call sites for extracted functions
- `_run_detection()`: 4 direct calls (lines 300, 703, 913, 965)
- `_resize_for_detect()`: 1 call (line 737, in auto_calibrate)
- `_finalize_detect_result()`: 3 calls (lines 707, 913, 969)

## Task 5: Backend preset CRUD API + config extension

### Context
- Added `import uuid` and `from datetime import datetime` to api.py
- Extracted inline `allowed` key set from `set_stream_detect_config()` into module-level `ALLOWED_DETECT_KEYS` constant for reuse by presets apply endpoint
- Added `defaults.setdefault("presets", [])` to `load_config()` for config.json schema
- Created 6 endpoints: GET/POST /api/presets, GET/PUT/DELETE /api/presets/{id}, POST /api/presets/{id}/apply
- Preset IDs use `uuid.uuid4().hex[:12]` (12-char short IDs)
- Duplicate name creates new ID but overwrites params (last-write-wins)
- Apply silently ignores unknown keys (filtered by ALLOWED_DETECT_KEYS), missing keys keep current values
- 16 new tests in edge/tests/test_presets.py covering full CRUD, duplicate overwrite, apply validation

### Dependencies
- Blocks: Tasks 8 (frontend preset UI), 12 (preset orchestration)

## Task 3: Enhanced 2D Kalman filter with cumulative angle unwrapping

### What changed
- `AngleKalman` in `gauge_reader/temporal.py`: 1D constant-position → 2D constant-velocity
- State vector: `[angle, angular_velocity]` (2D numpy array)
- Transition: `angle = angle + dt * velocity`, `velocity = velocity` (constant velocity)
- Measurement: angle only via `H = [[1, 0]]`
- Cumulative angle unwrapping: internal state is unbounded, output modulo [0, 360)
- Constructor: `R=0.5, Q=0.05, dt=0.2, Q_vel=0.01` (backward compat with scalar R/Q)
- New methods: `set_measurement_noise(R)`, `set_process_noise(Q_angle, Q_vel)`, `set_dt(dt)`
- Config: `angle_kalman_dt` (float, default 0.2) in `api.py`

### Angle unwrapping mechanism
- Predicted angle is taken modulo 360 for innovation computation
- Raw difference `measurement - predicted_mod` is unwrapped to [-180, 180)
- This unwrapped difference is the Kalman innovation → applied to unbounded state
- Result: 355° → 5° (innovation = +10°, not -350°), filtered output ≈ 358°
- Key insight: the innovation is always the SHORTEST angular path

### Matrix dimensions
- `F`: 2×2 `[[1, dt], [0, 1]]`
- `H`: 1×2 `[[1, 0]]`
- `Q`: 2×2 `[[Q_angle, 0], [0, Q_vel]]`
- `R`: 1×1 `[[R]]`
- `P`: 2×2 (initialized as identity)
- `K`: 2×1 (Kalman gain)
- State `x`: (2,) array `[angle, vel]`

### Velocity tracking observation
- With `dt=1.0` and `R=0.5, Q=0.05`, steady-state velocity tracks ~9.3 °/frame for a true 10 °/frame ramp (smoothing introduces lag)

### Backward compatibility
- Old `R` and `Q` config keys still work (mapped via setter methods)
- Old constructor call `AngleKalman(R=0.1, Q=0.01)` works — `dt` defaults to 0.2, `Q_vel` defaults to 0.01
- `_reinit_temporal()` uses setter methods instead of direct attribute assignment

### Test coverage (10 tests, all passing)
- 5 existing tests preserved (center tracker, Kalman smoothing/convergence/init)
- 5 new tests: constant velocity tracking, angle unwrapping across boundary, noise smoothing, backward compat, dt parameter

## Task 4: Define SLIDER_RANGES in index.html

### Schema
- `SLIDER_RANGES` constant added at line 1096 (between `toast()` and `checkHealth()`)
- 34 numeric params covered (all numeric fields from `getFormValues()` except checkboxes, selects, text inputs)
- 9 fields excluded: `point`, `camera_id`, `cam_resolution`, `detect_method` (selects); `use_clahe`, `circle_adaptive_thresh`, `cam_auto_exposure` (checkboxes); `server_api_url`, `api_key` (text)
- `angle_kalman_dt` does NOT exist in the codebase — not included
- `clahe_clip` and `clahe_tile` are real form fields (CLAHE main pipeline config) — included with ranges matching existing `<input type="range">` attributes
- Odd-only params: `blur_kernel` (step=2), `filter_window` (step=2), `threshold_block` (step=2) — validated in test

### Key ranges
| Param | Min | Max | Step |
|-------|-----|-----|------|
| min_value / max_value | -99999 | 99999 | 0.1 |
| min_angle / max_angle | 0 | 360 | 1 |
| blur_kernel | 1 | 31 | 2 |
| threshold_block | 0 | 99 | 2 |
| interval_seconds | 30 | 86400 | 30 |
| cam_exposure_absolute | -1 | 10000 | 10 |

### Test
- `edge/tests/test_slider_ranges.py` parses JS from index.html to extract both `SLIDER_RANGES` and `getFormValues()` structures
- 6 test methods: coverage, orphans, odd-only validation, exclusion check, count match, docstring presence
- All 6 passing

## Task 2: CLAHE clip/tile exposed to config

### Changes Made
- Added `clahe_clip` (float, default 2.0) and `clahe_tile` (int, default 8) to `load_config()` defaults in `app/api.py`
- Added both keys to `allowed` sets in `update_config()` and `set_stream_detect_config()`
- Modified `gauge_reader/preprocess.py:preprocess()` to accept `clahe_clip` and `clahe_tile` params, forwarded to `apply_clahe()`
- `_run_detection()` in api.py now passes config values to `preprocess()` (non-radial path) and to direct `createCLAHE()` (radial path)
- `/detect` and `/api/one-shot` endpoints accept `clahe_clip`/`clahe_tile` form params
- Added range slider inputs (type="range") in Detection card of index.html: CLAHE Clip (0.5-10, step 0.5), CLAHE Tile (2-16, step 2)
- Wired into all frontend paths: pollOverlay, startStreamDetection, callOneShot, getFormValues

### Key Decisions
- Used `<input type="range">` for sliders (not number inputs) per task spec
- Used `load_config()` defaults as the single source of truth; /api/one-shot merges on top
- Backward compat: preprocess() defaults clahe_clip=2.0, clahe_tile=8 match the old hardcoded values
- `circle_clahe_clip` kept separate — it controls circle detection CLAHE, not main pipeline CLAHE
- Tests: 3 new tests (defaults backward compat, clip changes output, tile changes output) — all 12 passing

## Task 1 Results

### What was done
- Created `gauge_reader/detector.py` with `GaugeDetector` class
- Class holds config, CenterTracker, AngleKalman (injectable for shared state)
- Public API: `detect(frame, config_overrides=None)`, `resize_for_detect(img)`, `finalize_result(...)`
- Internal `_run_detection()` has same logic as the original inline function
- Optional threading locks for thread-safe temporal state access
- Modified `app/api.py`:
  - Imports `GaugeDetector` from `gauge_reader.detector`
  - Global `_gauge_detector` lazy-initialized via `_get_gauge_detector()` — shares `_center_tracker`/`_angle_kalman` with existing globals
  - `_run_detection()` kept as backward-compat wrapper delegating to `_gauge_detector._run_detection(frame, cfg)`
  - Removed unused imports: angle_to_value, find_gauge_center_legacy, find_needle_angle_legacy, find_needle_angle, preprocess
  - `_resize_for_detect()` and `_finalize_detect_result()` remain as standalone functions (used by auto_calibrate and endpoints)
- Thread safety preserved: GaugeDetector accepts optional `center_tracker_lock`/`angle_kalman_lock`

### Test results
- 14 new test cases in `tests/test_detector.py` covering: import, instantiation, detect() output format, angle accuracy on synthetic images, config overrides, resize_for_detect, finalize_result
- All 83 tests pass (including 14 new + 69 existing)

### Key design decisions
- GaugeDetector accepts existing tracker/kalman via constructor for shared state with api.py globals
- Optional lock parameters (None = no locking for single-thread use)
- `_run_detection()` remains in api.py as thin wrapper for Task 11 backward compatibility
- `_DETECT_USE_W`/`_DETECT_MAX_W` kept as class constants (no external dependency on api.py globals)
- `_reinit_temporal()` continues to work via shared `_center_tracker`/`_angle_kalman` object references

## Task 11: Port push_readings.py to shared GaugeDetector

### What changed
- `push_readings.py` no longer has `detect_gauge()` — replaced by `GaugeDetector.detect()` + `finalize_result()`
- Imports reduced from 11 lines to 2:`from gauge_reader.detector import GaugeDetector` + `ValueFilter`
- Removed imports: base64, numpy, angle_to_value, find_gauge_center, find_gauge_center_legacy, find_needle_angle_legacy, draw_needle, find_needle_angle, preprocess, CenterTracker, AngleKalman
- Removed `_DETECT_USE_W = 320` constant — GaugeDetector uses internal `_DETECT_USE_W = 480`
- `do_reading()` takes `detector` instead of `center_tracker`+`angle_kalman`
- `main()` creates `GaugeDetector(config)` once (owns internal CenterTracker/AngleKalman across loop iterations)
- `do_reading()` calls `detector.detect(frame)` → `detector.finalize_result(result, frame, 1.0, config)` for annotated_image
- `ValueFilter` stays in push_readings.py (not part of GaugeDetector)

### Key design decisions
- GaugeDetector owns its temporal state (CenterTracker/AngleKalman) internally — no need to create them in `main()`
- `finalize_result()` used to get `annotated_image` for server payload (detect() returns debug images, not base64 JPEG)
- `upscale=1.0` passed to `finalize_result()` because `detect()` already upscales coords internally
- Old `_DETECT_USE_W = 320` was actually a bug (commented "matches api.py" but api.py uses 480) — using GaugeDetector's 480 fixes it

### Test results
- 10 new test cases in `tests/test_push_readings.py` covering: import assertions, output format, consistency, CLI
- All 93 tests pass (10 new + 83 existing)

## Task 9: Slider controls replacing number inputs

### What changed
- All 34 numeric `<input type="number">` fields in index.html converted to `<input type="range">` sliders
- Each slider has: visible range input + `<span class="slider-value">` value label + hidden `<input type="number" style="display:none">` for JS compatibility
- 2 existing range sliders (clahe_clip, clahe_tile) enhanced with value labels and oninput handlers
- Slider min/max/step sourced from `SLIDER_RANGES` constant (already defined in Task 4)
- CSS: MD3 teal accent (#14b8a6) thumb/track with hover scale(1.2) and focus ring glow
- `.slider-container` flex layout for range + label horizontal alignment

### Key design decisions
- Hidden number input (`id="fieldname"`) keeps same ID so `getFormValues()`, `loadConfig()`, `saveConfig()` work unchanged
- Slider gets ID `fieldname_slider` with oninput wiring `onSliderInput(this, 'fieldname')`
- `onSliderInput()` updates hidden input value + value label, then calls `debouncedUpdateStreamConfig()`
- Debounce at 300ms — calls `startStreamDetection()` when stream detection is active
- `refreshSliders()` iterates `Object.keys(SLIDER_RANGES)` — syncs slider positions from hidden inputs
- For clahe_clip/clahe_tile: element IS the range slider (no hidden input), `refreshSliders()` skips the hidden→slider copy but still updates label

### JavaScript functions added
- `onSliderInput(slider, fieldId)` — slider event handler
- `debouncedUpdateStreamConfig()` — 300ms debounce → POST to /api/stream-detect-config
- `refreshSliders()` — sync all sliders from current form values

### Wire points
- `loadConfig()` → sets values from API → calls `refreshSliders()`
- `saveConfig()` → saves to API → calls `refreshSliders()`
- `init()` → after `loadConfig()` → calls `refreshSliders()`
- `fillPointValues()` → sets min/max from point → calls `refreshSliders()`
- `autoCalibrate()` → sets angles from auto-cal → calls `refreshSliders()`
- `applyCalibration()` → sets angles from manual cal → calls `refreshSliders()`

### Fields excluded (not converted)
- Checkboxes: use_clahe, circle_adaptive_thresh, cam_auto_exposure
- Selects: point, camera_id, cam_resolution, detect_method
- Text inputs: server_api_url, api_key

### Test coverage
- 11 new tests in `tests/test_slider_html.py` covering: slider existence, value labels, oninput handlers, hidden inputs, min/max/step matching, getFormValues() compatibility, refreshSliders function, debounce config
- All 104 tests pass (11 new + 93 existing)
