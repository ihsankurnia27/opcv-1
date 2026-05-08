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

from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle


def main():
    parser = argparse.ArgumentParser(description="Read analog gauge value from image.")
    parser.add_argument("image_path", help="Path to gauge image file")
    parser.add_argument("--min-value", type=float, default=0.0, help="Minimum gauge value")
    parser.add_argument("--max-value", type=float, default=100.0, help="Maximum gauge value")
    parser.add_argument("--min-angle", type=float, default=45.0, help="Angle at minimum value (degrees)")
    parser.add_argument("--max-angle", type=float, default=315.0, help="Angle at maximum value (degrees)")
    parser.add_argument("--center-offset-y", type=float, default=0.0, help="Vertical center offset (px, positive=down)")
    parser.add_argument("--inner-ratio", type=float, default=0.60, help="Inner sampling radius ratio")
    parser.add_argument("--outer-ratio", type=float, default=0.80, help="Outer sampling radius ratio")
    parser.add_argument("--blur-kernel", type=int, default=5, help="Gaussian blur kernel size (0=skip)")
    parser.add_argument("--threshold-block", type=int, default=0, help="Adaptive threshold block size (0=skip)")
    parser.add_argument("--threshold-c", type=int, default=5, help="Adaptive threshold C constant")
    parser.add_argument("--save-annotated", help="Save annotated image to this path")
    args = parser.parse_args()

    img = cv2.imread(args.image_path)
    if img is None:
        print(json.dumps({"error": f"cannot read image: {args.image_path}"}))
        sys.exit(1)

    center = find_gauge_center(img)
    if center is None:
        print(json.dumps({"error": "could not find gauge center"}))
        sys.exit(1)

    cx, cy, radius = center
    cy += int(args.center_offset_y)
    angle_deg = find_needle_angle(img, cx, cy, radius,
                                   inner_ratio=args.inner_ratio,
                                   outer_ratio=args.outer_ratio,
                                   blur_kernel=args.blur_kernel,
                                   threshold_block=args.threshold_block,
                                   threshold_c=args.threshold_c)

    # map angle -> value (with wrap-around support)
    old_range = args.max_angle - args.min_angle
    new_range = args.max_value - args.min_value
    if args.min_angle <= args.max_angle:
        if old_range == 0:
            value = args.min_value
        else:
            value = ((angle_deg - args.min_angle) * new_range) / old_range + args.min_value
    else:
        # wrap around 0: gauge sweeps past right (0°)
        full_range = (360 - args.min_angle) + args.max_angle
        if full_range == 0:
            value = args.min_value
        else:
            if angle_deg >= args.min_angle:
                needle_pos = angle_deg - args.min_angle
            else:
                needle_pos = (360 - args.min_angle) + angle_deg
            value = (needle_pos * new_range) / full_range + args.min_value
    value = max(args.min_value, min(args.max_value, value))

    annotated_path = None
    if args.save_annotated:
        annotated = draw_needle(img.copy(), cx, cy, radius, angle_deg)
        # draw min/max angle reference lines
        ref_len = radius * 0.7
        for a, clr in [(args.min_angle, (255, 255, 0)), (args.max_angle, (255, 255, 0))]:
            rad = np.deg2rad(a)
            x2 = int(cx + ref_len * np.cos(rad))
            y2 = int(cy + ref_len * np.sin(rad))
            cv2.line(annotated, (cx, cy), (x2, y2), clr, 2)
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
