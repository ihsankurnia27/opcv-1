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


def test_angle_kalman_tracks_constant_velocity():
    """Kalman with dt=1 should track a needle moving 5 deg/frame."""
    kf = AngleKalman(R=0.5, Q=0.05, dt=1.0)
    measurements = list(range(0, 50, 5))  # 0, 5, 10, ... 45
    outputs = [kf.update(m) for m in measurements]
    # After initial convergence, track within tolerance
    for i in range(5, 10):
        err = abs(outputs[i] - measurements[i])
        assert err < 5.0, f"Vel tracking fail at step {i}: {outputs[i]:.2f} vs {measurements[i]}"


def test_angle_kalman_unwraps_across_boundary():
    """355° → 5° should be a +10° correction (through 360), not -350°."""
    kf = AngleKalman(R=0.5, Q=0.05, dt=0.2)
    kf.update(355.0)
    for _ in range(15):
        kf.update(355.0)
    # State converged near 355; internal unwrapped angle is still ~355
    internal_before = kf._x[0]
    result = kf.update(5.0)
    internal_after = kf._x[0]
    # Internal unwrapped angle should have INCREASED (went through 0, not backward)
    assert internal_after > internal_before, \
        f"Unwrapped angle decreased: {internal_after:.2f} <= {internal_before:.2f}"
    # Output modulo 360 should be near 0/360 boundary
    assert 350.0 <= result <= 360.0 or 0.0 <= result <= 10.0, \
        f"Output {result:.2f} not near 0/360 boundary"


def test_angle_kalman_smooths_noise():
    """Output variance should be less than input measurement variance."""
    rng = np.random.default_rng(42)
    kf = AngleKalman(R=0.5, Q=0.05)
    kf.update(90.0)
    kf.update(90.0)
    noise = rng.normal(0, 5, 50)
    noisy = [90.0 + n for n in noise]
    outputs = [kf.update(m) for m in noisy]
    assert float(np.var(outputs)) < float(np.var(noisy)), \
        f"Output var {np.var(outputs):.2f} >= input var {np.var(noisy):.2f}"


def test_angle_kalman_backward_compat_R_Q():
    """Old-style scalar R and Q constructor args still work."""
    kf = AngleKalman(R=0.1, Q=0.01)
    assert kf.R.shape == (1, 1)
    assert abs(kf.R[0, 0] - 0.1) < 1e-9
    assert abs(kf.Q_angle - 0.01) < 1e-9
    assert kf.update(45.0) == 45.0
    val = kf.update(46.0)
    assert 45.0 < val < 46.0, f"Backward compat failed: {val}"


def test_angle_kalman_dt_affects_response():
    """Different dt values produce measurably different filter response."""
    dt_small = 0.1
    dt_large = 2.0
    kf1 = AngleKalman(R=0.5, Q=0.05, dt=dt_small)
    kf2 = AngleKalman(R=0.5, Q=0.05, dt=dt_large)
    kf1.update(0.0)
    kf2.update(0.0)
    # Feed same ramp of measurements
    ramp = [0, 10, 20, 30, 40, 50]
    out1 = [kf1.update(m) for m in ramp]
    out2 = [kf2.update(m) for m in ramp]
    # Totals should differ due to dt affecting prediction step
    total1 = sum(out1)
    total2 = sum(out2)
    assert abs(total1 - total2) > 0.01, \
        f"dt {dt_small} sum {total1:.2f} vs dt {dt_large} sum {total2:.2f}"
