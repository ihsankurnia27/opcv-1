"""Temporal filtering: center position EMA + 1D Kalman angle filter."""

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
    """1D Kalman filter (constant position model) for needle angle smoothing.

    State: [angle]
    Predict: x = x (needle assumed stationary between frames)
    Update:  x = x + K * (measurement - x)
    """

    def __init__(self, R=0.1, Q=0.01):
        self.R = R  # measurement noise
        self.Q = Q  # process noise
        self._x = None  # state estimate
        self._P = None  # error covariance

    def update(self, measurement):
        measurement = float(measurement)
        if self._x is None:
            self._x = measurement
            self._P = 1.0
            return measurement

        # Predict
        x_pred = self._x
        P_pred = self._P + self.Q

        # Update
        K = P_pred / (P_pred + self.R)
        self._x = x_pred + K * (measurement - x_pred)
        self._P = (1 - K) * P_pred

        return float(self._x)

    def reset(self):
        self._x = None
        self._P = None
