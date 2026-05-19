# Design Spec: Adjustable Circle Detection Parameters

Date: 2026-05-19
Topic: Adjustable Circle Detection Parameters for Edge Gauge Reader

## 1. Problem Statement
The circle detection algorithm in `edge/gauge_reader/find_gauge_center.py` currently uses hardcoded parameters for Hough Circle transformation and contour circularity filtering. In challenging lighting or varying gauge sizes, these fixed values can prevent the system from finding the gauge center, and users currently have no way to tune these values via the UI or config.

## 2. Proposed Changes

### A. Engine Updates (`edge/gauge_reader/find_gauge_center.py`)
- Modify `_hough_circles`, `_contour_circularity`, and `find_gauge_center` to accept parameters instead of using hardcoded constants.
- Provide sensible defaults (the current hardcoded values) for backward compatibility.

### B. API Updates (`edge/app/api.py`)
- Update `load_config()` to include the 7 new keys with their defaults.
- Update `/api/config` and `/api/stream-detect-config` allowed keys list to include:
    - `circle_hough_param1`
    - `circle_hough_param2`
    - `circle_hough_dp`
    - `circle_min_circularity`
    - `circle_min_dist_ratio`
    - `circle_min_radius_ratio`
    - `circle_max_radius_ratio`

### C. UI Updates (`edge/app/static/index.html`)
- Add a new **Circle Tuning** card in the configuration sidebar.
- Update the **Tuning Guide** section with instructions for these new parameters.
- Update JavaScript `loadConfig`, `saveConfig`, and `startStreamDetection` to handle the new fields.

## 3. Configuration Schema
| Config Key | Default | Description |
| :--- | :--- | :--- |
| `circle_hough_param1` | `100` | Higher threshold for Canny edge detector. |
| `circle_hough_param2` | `50` | Accumulator threshold (Sensitivity). Lower is more sensitive. |
| `circle_hough_dp` | `1.2` | Inverse ratio of the accumulator resolution to the image resolution. |
| `circle_min_circularity` | `0.7` | Minimum circularity score ($4\pi \times Area / Perimeter^2$) for contour fallback. |
| `circle_min_dist_ratio` | `0.3` | Minimum distance between circle centers as a ratio of image height. |
| `circle_min_radius_ratio`| `0.05` | Minimum circle radius as a ratio of image width. |
| `circle_max_radius_ratio`| `0.45` | Maximum circle radius as a ratio of image width. |

## 4. Verification Plan
1. **API Verification**: Use `curl` to verify that the new keys are accepted and persisted in `config.json`.
2. **Detection Verification**: Tune the parameters via the UI and observe the effect on the "Binary + Ann" stream view.
3. **Robustness**: Verify that detection still works with defaults if the new keys are missing from `config.json`.
