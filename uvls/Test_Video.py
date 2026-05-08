#!/usr/bin/env python3
"""Live gauge reader from camera using radial sampling approach.

Imports gauge_reader modules (find_gauge_center, find_needle_radial, value_filter).
Keeps camera capture loop and temporal smoothing.
"""

import sys
import time

import cv2
import numpy as np

from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle
from gauge_reader.value_filter import ValueFilter


def main():
    print("Gauge Meter Reader — Live Camera")
    print("Enter gauge parameters:")

    min_angle = float(input("Min angle (degrees): ") or 45)
    max_angle = float(input("Max angle (degrees): ") or 315)
    min_value = float(input("Min value: ") or 0)
    max_value = float(input("Max value: ") or 10)
    units = input("Units: ") or "bar"

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: cannot open camera")
        sys.exit(1)

    vf = ValueFilter(median_window_size=5, ema_alpha=0.15, max_jump=1.5)

    print("\nPress 'q' to quit, 'l' to lock/unlock gauge center, 'r' to reset lock")

    locked_center = None  # (cx, cy, radius) when locked
    center = None

    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            print("Camera read error")
            break

        display = img.copy()

        if locked_center:
            center = locked_center
        else:
            center = find_gauge_center(img)

        if center:
            cx, cy, radius = center

            # Draw center + circle
            cv2.circle(display, (cx, cy), radius, (0, 0, 255), 2)
            cv2.circle(display, (cx, cy), 3, (0, 255, 0), -1)

            angle_deg = find_needle_angle(img, cx, cy, radius)

            # Map angle to value
            old_range = max_angle - min_angle
            new_range = max_value - min_value
            if old_range == 0:
                raw_value = min_value
            else:
                raw_value = ((angle_deg - min_angle) * new_range) / old_range + min_value
                raw_value = max(min_value, min(max_value, raw_value))

            # Temporal smoothing
            stable = vf.add(raw_value)

            # Draw needle
            display = draw_needle(display, cx, cy, radius, angle_deg)

            # Show value overlay
            cv2.putText(display, f"{stable:.2f} {units}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display, f"Angle: {angle_deg:.1f} deg",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            if locked_center:
                cv2.putText(display, "LOCKED", (display.shape[1] - 100, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            cv2.putText(display, "No gauge detected",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Analog Gauge Reader", display)
        key = cv2.waitKey(30) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('l'):
            if center and not locked_center:
                locked_center = center
                print("Center LOCKED")
            elif locked_center:
                locked_center = None
                print("Center UNLOCKED")
        elif key == ord('r'):
            locked_center = None
            vf = ValueFilter(median_window_size=5, ema_alpha=0.15, max_jump=1.5)
            print("Reset")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
