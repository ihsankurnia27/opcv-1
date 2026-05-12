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
