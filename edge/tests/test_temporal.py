import numpy as np
from gauge_reader.temporal import CenterTracker, AngleKalman


def test_center_tracker_ema_converges():
    tracker = CenterTracker(ema_alpha=0.3)
    # Feed same center 10 times
    for _ in range(10):
        tracker.update(100, 200, 150)
    cx, cy, r = tracker.get()
    assert abs(cx - 100) < 2, f"EMA should converge near 100, got {cx}"
    assert abs(cy - 200) < 2
    assert abs(r - 150) < 2


def test_center_tracker_rejects_none_when_uninitialized():
    tracker = CenterTracker(ema_alpha=0.3)
    cx, cy, r = tracker.get()
    assert cx == 0 and cy == 0 and r == 0


def test_angle_kalman_smooths_jumps():
    kf = AngleKalman(R=0.1, Q=0.01)
    # Initialize
    init = kf.update(45.0)
    assert init == 45.0
    # Small change tracked
    a1 = kf.update(46.0)
    assert 45.0 < a1 < 46.0, f"Kalman should smooth step, got {a1}"


def test_angle_kalman_converges_to_constant():
    kf = AngleKalman(R=0.1, Q=0.01)
    kf.update(90.0)
    for _ in range(20):
        result = kf.update(90.0)
    assert abs(result - 90.0) < 0.5, f"Should converge to constant 90, got {result}"


def test_angle_kalman_initial_measurement_sets_state():
    kf = AngleKalman(R=0.1, Q=0.01)
    result = kf.update(270.0)
    assert result == 270.0
