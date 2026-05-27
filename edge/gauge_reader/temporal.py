"""Temporal filtering: center position EMA + 2D Kalman angle filter with unwrapping."""

import numpy as np


class CenterTracker:
    """EMA smoothing on gauge center (cx, cy, radius) across frames."""

    def __init__(self, ema_alpha=0.3):
        self.alpha = ema_alpha
        self._cx = 0.0
        self._cy = 0.0
        self._radius = 0.0
        self._initialized = False

    def update(self, cx, cy, radius):
        if not self._initialized:
            self._cx = float(cx)
            self._cy = float(cy)
            self._radius = float(radius)
            self._initialized = True
        else:
            self._cx = self.alpha * cx + (1 - self.alpha) * self._cx
            self._cy = self.alpha * cy + (1 - self.alpha) * self._cy
            self._radius = self.alpha * radius + (1 - self.alpha) * self._radius

    def get(self):
        return self._cx, self._cy, self._radius

    @property
    def initialized(self):
        return self._initialized

    def reset(self):
        self.__init__(self.alpha)


class AngleKalman:
    """2D Kalman filter (constant velocity model) for needle angle smoothing.

    State: [angle, angular_velocity]
      angle  = angle + dt * angular_velocity   (constant velocity transition)
      vel    = vel                              (unchanged)

    Measurement: angle only (H = [[1, 0]])

    Features cumulative angle unwrapping: internal angle is unbounded,
    output is converted to [0, 360) via modulo.  This means 355 -> 5
    produces a small +10deg correction instead of a large -350deg jump.
    """

    def __init__(self, R=0.5, Q=0.05, dt=0.2, Q_vel=0.01):
        self.R = np.array([[R]])       # measurement noise (1x1)
        self.Q_angle = Q               # process noise for angle
        self.Q_vel = Q_vel             # process noise for angular velocity
        self.dt = dt                   # time step (seconds)
        self.H = np.array([[1.0, 0.0]])  # measurement matrix (1x2)
        self._x = None                 # state [angle, vel] (unwrapped)
        self._P = None                 # error covariance (2x2)

    def _F(self):
        return np.array([[1.0, self.dt],
                         [0.0, 1.0]])

    def _Q(self):
        return np.array([[self.Q_angle, 0.0],
                         [0.0, self.Q_vel]])

    @staticmethod
    def _unwrap_diff(raw_diff):
        """Unwrap an angular difference to [-180, 180)."""
        if raw_diff > 180.0:
            raw_diff -= 360.0
        elif raw_diff < -180.0:
            raw_diff += 360.0
        return raw_diff

    def update(self, measurement):
        measurement = float(measurement)

        if self._x is None:
            self._x = np.array([measurement, 0.0])
            self._P = np.eye(2)
            return measurement

        F = self._F()
        x_pred = F @ self._x
        P_pred = F @ self._P @ F.T + self._Q()

        predicted_angle_mod = x_pred[0] % 360.0
        raw_diff = measurement - predicted_angle_mod
        y = np.array([self._unwrap_diff(raw_diff)])

        S = self.H @ P_pred @ self.H.T + self.R
        K = P_pred @ self.H.T @ np.linalg.inv(S)
        self._x = x_pred + (K @ y).flatten()
        self._P = (np.eye(2) - K @ self.H) @ P_pred

        return float(self._x[0] % 360.0)

    def reset(self):
        self._x = None
        self._P = None

    def set_measurement_noise(self, R):
        """Update measurement noise covariance (scalar → 1x1 matrix)."""
        self.R = np.array([[R]])

    def set_process_noise(self, Q_angle=None, Q_vel=None):
        """Update process noise covariance components (each is a scalar)."""
        if Q_angle is not None:
            self.Q_angle = Q_angle
        if Q_vel is not None:
            self.Q_vel = Q_vel

    def set_dt(self, dt):
        """Update time step — F matrix is rebuilt lazily on next predict."""
        self.dt = dt
