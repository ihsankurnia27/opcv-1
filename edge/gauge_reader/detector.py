"""GaugeDetector — encapsulated gauge detection pipeline.

Extracted from app/api.py to allow reuse by:
  - app/api.py      (FastAPI endpoints, stream detect)
  - push_readings.py (scheduled push reader, Task 11)

Usage:
    detector = GaugeDetector(config_dict)
    result = detector.detect(frame)
    # or with per-call overrides:
    result = detector.detect(frame, config_overrides={"blur_kernel": 7})
"""

import contextlib

import cv2
import numpy as np

from gauge_reader import angle_to_value
from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle import find_needle_angle
from gauge_reader.find_needle_radial import find_needle_angle as find_needle_angle_legacy
from gauge_reader.draw import draw_needle
from gauge_reader.preprocess import preprocess
from gauge_reader.temporal import CenterTracker, AngleKalman


class GaugeDetector:
    """Detect gauge needle angle/value from a camera frame.

    Encapsulates the full pipeline: resize → preprocess → center detection →
    needle detection → angle Kalman filter → value conversion → debug images.

    Holds internal state (CenterTracker, AngleKalman) across ``detect()`` calls
    for temporal smoothing.  Call ``detect()`` repeatedly with successive frames
    to benefit from filtering.
    """

    # Detection resolution for speed — internal CV ops run at this size.
    _DETECT_USE_W = 480
    # Max dimension for auto-calibrate resize.
    _DETECT_MAX_W = 640

    def __init__(self, config=None, center_tracker=None, angle_kalman=None,
                 center_tracker_lock=None, angle_kalman_lock=None):
        self._config = config if config is not None else {}

        # Temporal state — caller may inject existing objects for shared state
        if center_tracker is not None:
            self._center_tracker = center_tracker
        else:
            self._center_tracker = CenterTracker(
                ema_alpha=float(self._config.get("center_ema", 0.3))
            )
        if angle_kalman is not None:
            self._angle_kalman = angle_kalman
        else:
            self._angle_kalman = AngleKalman(
                R=float(self._config.get("angle_kalman_R", 0.1)),
                Q=float(self._config.get("angle_kalman_Q", 0.01)),
            )
        # Optional locks for thread-safe access when injected objects are
        # shared across threads (e.g., api.py background reader).
        self._center_tracker_lock = center_tracker_lock
        self._angle_kalman_lock = angle_kalman_lock

    # ── public API ──────────────────────────────────────────────

    def detect(self, frame, config_overrides=None):
        """Run full gauge detection pipeline.

        Args:
            frame: BGR numpy array (any resolution).
            config_overrides: optional dict of per-call overrides merged on
                top of the base config passed at construction.  Used by
                ``/api/stream-detect-config``.

        Returns:
            dict with keys:
                value, angle, center (dict with x/y/radius), error, w, h,
                debug_preprocess, debug_binary, debug_preprocess_ann,
                debug_binary_ann
        """
        cfg = {**self._config, **(config_overrides or {})}
        return self._run_detection(frame, cfg)

    def resize_for_detect(self, img):
        """Resize large images down to ``_DETECT_MAX_W`` for faster CV ops.

        Returns:
            (resized_img, upscale_factor)
            upscale_factor is 1.0 if unchanged, >1.0 to restore original size.
        """
        h, w = img.shape[:2]
        if max(w, h) <= self._DETECT_MAX_W:
            return img, 1.0
        scale = self._DETECT_MAX_W / max(w, h)
        return (
            cv2.resize(img, (int(w * scale), int(h * scale)),
                       interpolation=cv2.INTER_AREA),
            1.0 / scale,
        )

    def finalize_result(self, result, full_img, upscale, cfg,
                        need_annotation=True):
        """Strip debug images, upscale coords, optionally annotate.

        Args:
            result: raw dict from ``detect()`` (contains debug images).
            full_img: original full-resolution frame (for annotation).
            upscale: factor to multiply detection coords by.
            cfg: config dict (needed for draw_needle parameters).
            need_annotation: if True, encode annotated JPG as base64.

        Returns:
            result dict with debug images removed and ``annotated_image`` added.
        """
        # Strip debug images — numpy arrays not JSON-serializable
        for key in ["debug_preprocess", "debug_binary",
                     "debug_preprocess_ann", "debug_binary_ann"]:
            result.pop(key, None)

        ctr = result["center"]
        ctr["x"] = int(ctr["x"] * upscale)
        ctr["y"] = int(ctr["y"] * upscale)
        ctr["radius"] = int(ctr["radius"] * upscale)
        result["center"] = ctr

        h_full, w_full = full_img.shape[:2]
        result["w"] = w_full
        result["h"] = h_full

        if need_annotation:
            angle_deg = float(result["angle"])
            annotated = draw_needle(
                full_img.copy(),
                ctr["x"], ctr["y"], ctr["radius"], angle_deg,
                inner_ratio=float(cfg["inner_ratio"]),
                outer_ratio=float(cfg["outer_ratio"]),
                min_angle=float(cfg["min_angle"]),
                max_angle=float(cfg["max_angle"]),
            )
            _, ann_buf = cv2.imencode(".jpg", annotated,
                                      [cv2.IMWRITE_JPEG_QUALITY, 85])
            import base64
            result["annotated_image"] = base64.b64encode(ann_buf).decode()
        else:
            result["annotated_image"] = None

        return result

    # ── internal pipeline ──────────────────────────────────────

    def _run_detection(self, frame, cfg):
        """Internal: detect gauge with the given (merged) config."""
        if frame is None:
            return {"error": "no frame provided"}
        if frame.size == 0:
            return {"error": "empty frame"}
        method = cfg.get("detect_method", "auto")
        use_clahe = cfg.get("use_clahe", True)

        h_orig, w_orig = frame.shape[:2]
        if max(w_orig, h_orig) > self._DETECT_USE_W:
            scale = self._DETECT_USE_W / max(w_orig, h_orig)
            small = cv2.resize(
                frame,
                (int(w_orig * scale), int(h_orig * scale)),
                interpolation=cv2.INTER_AREA,
            )
        else:
            scale = 1.0
            small = frame

        # ── Preprocess ──────────────────────────────────────
        if method != "radial":
            proc = preprocess(small, clahe=use_clahe, denoise=True)
        else:
            proc = small
            if use_clahe:
                gray_proc = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray_proc)
                proc = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        debug_proc = proc.copy()

        # ── Center detection ────────────────────────────────
        if method == "radial":
            center_result = find_gauge_center_legacy(
                proc,
                circle_hough_dp=float(cfg.get("circle_hough_dp", 1)),
                circle_hough_param1=float(cfg.get("circle_hough_param1", 100)),
                circle_hough_param2=float(cfg.get("circle_hough_param2", 50)),
                circle_min_radius_ratio=float(
                    cfg.get("circle_min_radius_ratio", 0.05)),
                circle_max_radius_ratio=float(
                    cfg.get("circle_max_radius_ratio", 0.45)),
                circle_min_dist_ratio=float(
                    cfg.get("circle_min_dist_ratio", 0.3)),
            )
            if center_result is None:
                return {"error": "could not find gauge center"}
            cx, cy, radius = center_result
        else:
            with (self._center_tracker_lock
                  if self._center_tracker_lock is not None
                  else contextlib.nullcontext()):
                prev = (self._center_tracker.get()
                        if self._center_tracker.initialized
                        else None)
            center_result = find_gauge_center(
                proc, prev_center=prev,
                ema_alpha=float(cfg.get("center_ema", 0.3)),
                use_clahe=False,
                circle_hough_param1=float(
                    cfg.get("circle_hough_param1", 100)),
                circle_hough_param2=float(
                    cfg.get("circle_hough_param2", 50)),
                circle_hough_dp=float(cfg.get("circle_hough_dp", 1.2)),
                circle_canny_low=int(cfg.get("circle_canny_low", 50)),
                circle_canny_high=int(cfg.get("circle_canny_high", 150)),
                circle_adaptive_thresh=bool(
                    cfg.get("circle_adaptive_thresh", False)),
                circle_dilate=int(cfg.get("circle_dilate", 0)),
                circle_clahe_clip=float(
                    cfg.get("circle_clahe_clip", 2.0)),
                circle_min_circularity=float(
                    cfg.get("circle_min_circularity", 0.7)),
                circle_min_dist_ratio=float(
                    cfg.get("circle_min_dist_ratio", 0.3)),
                circle_min_radius_ratio=float(
                    cfg.get("circle_min_radius_ratio", 0.05)),
                circle_max_radius_ratio=float(
                    cfg.get("circle_max_radius_ratio", 0.45)),
            )
            if center_result is None:
                return {"error": "could not find gauge center"}
            cx, cy, radius = center_result
            with (self._center_tracker_lock
                  if self._center_tracker_lock is not None
                  else contextlib.nullcontext()):
                self._center_tracker.update(cx, cy, radius)

        cy_adjusted = cy + int(cfg["center_offset_y"])

        # ── ROI crop (optional, before needle detection) ────
        roi_dx = 0
        roi_dy = 0
        roi_enabled = cfg.get("use_roi", False)
        if isinstance(roi_enabled, str):
            roi_enabled = roi_enabled.lower() in ("1", "true")
        if roi_enabled:
            margin_val = float(cfg.get("roi_margin", 1.5))
            x1 = max(0, int(cx - radius * margin_val))
            y1 = max(0, int(cy - radius * margin_val))
            x2 = min(proc.shape[1], int(cx + radius * margin_val))
            y2 = min(proc.shape[0], int(cy + radius * margin_val))
            cropped = proc[y1:y2, x1:x2].copy()
            cx -= x1
            cy -= y1
            cy_adjusted = cy + int(cfg["center_offset_y"])
            proc = cropped
            if debug_proc is not None:
                debug_proc = debug_proc[y1:y2, x1:x2].copy()
            roi_dx = x1
            roi_dy = y1

        # ── Needle detection ────────────────────────────────
        debug_binary = None
        line_confidence_val = 0.0
        radial_confidence_val = 0.0
        strategy_consensus_val = 0.0
        if method == "radial":
            angle_deg = find_needle_angle_legacy(
                proc, cx, cy_adjusted, radius,
                inner_ratio=float(cfg["inner_ratio"]),
                outer_ratio=float(cfg["outer_ratio"]),
                blur_kernel=int(cfg["blur_kernel"]),
                threshold_block=int(cfg["threshold_block"]),
                threshold_c=int(cfg["threshold_c"]),
            )
            # Single strategy — moderate default confidence
            radial_confidence_val = 0.5
            strategy_consensus_val = 0.5
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
            )
            if "error" in angle_result:
                return angle_result
            angle_deg = float(angle_result["angle"])
            # Extract per-strategy confidences from angle_result
            radial_confidence_val = angle_result.get("radial_confidence") or 0.0
            line_confidence_val = angle_result.get("line_confidence") or 0.0
            strategy_consensus_val = angle_result.get("strategy_consensus", 0.0)

        # ── Temporal angle filter ───────────────────────────
        if method != "radial":
            with (self._angle_kalman_lock
                  if self._angle_kalman_lock is not None
                  else contextlib.nullcontext()):
                angle_deg = self._angle_kalman.update(angle_deg)

        # ── Upscale coords ──────────────────────────────────
        inv = 1.0 / scale if scale != 1.0 else 1.0
        cx_out = int((cx + roi_dx) * inv)
        cy_out = int((cy_adjusted + roi_dy) * inv)
        radius_out = int(radius * inv)

        # ── Debug images (at detection resolution) ──────────
        gray = cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)
        if int(cfg["blur_kernel"]) > 0:
            k = int(cfg["blur_kernel"])
            k = k if k % 2 == 1 else k + 1
            gray = cv2.GaussianBlur(gray, (k, k), 0)

        if int(cfg["threshold_block"]) > 0:
            b = int(cfg["threshold_block"])
            b = b if b % 2 == 1 else b + 1
            debug_binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY, b, int(cfg["threshold_c"]),
            )
        else:
            debug_binary = gray

        if debug_proc is not None:
            debug_proc = cv2.cvtColor(debug_proc, cv2.COLOR_BGR2GRAY)

        ann_proc = draw_needle(
            cv2.cvtColor(debug_proc, cv2.COLOR_GRAY2BGR),
            cx, cy_adjusted, radius, angle_deg,
            inner_ratio=float(cfg["inner_ratio"]),
            outer_ratio=float(cfg["outer_ratio"]),
            min_angle=float(cfg["min_angle"]),
            max_angle=float(cfg["max_angle"]),
        )
        ann_binary = draw_needle(
            cv2.cvtColor(debug_binary, cv2.COLOR_GRAY2BGR),
            cx, cy_adjusted, radius, angle_deg,
            inner_ratio=float(cfg["inner_ratio"]),
            outer_ratio=float(cfg["outer_ratio"]),
            min_angle=float(cfg["min_angle"]),
            max_angle=float(cfg["max_angle"]),
        )

        # ── Value conversion ────────────────────────────────
        min_a, max_a = float(cfg["min_angle"]), float(cfg["max_angle"])
        min_v, max_v = float(cfg["min_value"]), float(cfg["max_value"])
        value = angle_to_value(angle_deg, min_a, max_a, min_v, max_v)

        # ── Confidence computation ──────────────────────────
        combined = (radial_confidence_val + line_confidence_val
                    + strategy_consensus_val) / 3.0

        # ── Rejection logic ─────────────────────────────────
        min_conf = float(cfg.get("min_confidence", 0.0))
        rejected = bool(min_conf > 0 and combined < min_conf)

        return {
            "value": round(value, 2),
            "angle": round(angle_deg, 2),
            "confidence": round(combined, 3),
            "rejected": rejected,
            "center": {"x": cx_out, "y": cy_out, "radius": radius_out},
            "error": None,
            "w": w_orig, "h": h_orig,
            "debug_preprocess": debug_proc,
            "debug_binary": debug_binary,
            "debug_preprocess_ann": ann_proc,
            "debug_binary_ann": ann_binary,
        }
