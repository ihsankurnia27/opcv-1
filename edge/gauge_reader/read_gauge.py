#!/usr/bin/env python3
"""CLI wrapper: read gauge value from image file.

Usage:
    python3 read_gauge.py <image_path> --min-value 0 --max-value 10
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np

# Make package imports work when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gauge_reader import angle_to_value
from gauge_reader.preprocess import preprocess
from gauge_reader.find_gauge_center import find_gauge_center, find_gauge_center_legacy
from gauge_reader.find_needle_radial import find_needle_angle as find_needle_angle_legacy
from gauge_reader.find_needle import find_needle_angle
from gauge_reader.draw import draw_needle


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

    use_clahe = not args.no_clahe

    # Preprocess
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
        center_result = find_gauge_center(proc, prev_center=None, use_clahe=False)
        if center_result is None:
            print(json.dumps({"error": "could not find gauge center"}))
            sys.exit(1)
        cx, cy, radius = center_result

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
                                   max_angle=args.max_angle)
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


if __name__ == "__main__":
    main()
