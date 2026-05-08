import numpy as np


class ValueFilter:
    """Temporal smoothing: median filter + EMA + spike rejection.

    Direct port of the JS ValueFilter class from testing.php.
    """

    def __init__(self, median_window_size=5, ema_alpha=0.15, max_jump=1.5):
        self.raw_buffer = []
        self.median_window_size = median_window_size
        self.ema_alpha = ema_alpha
        self.current_ema = None
        self.max_jump = max_jump
        self.consecutive_jumps = 0

    def update_params(self, alpha, jump):
        self.ema_alpha = alpha
        self.max_jump = jump

    def add(self, raw_value):
        # A. Spike rejection
        if self.current_ema is not None:
            if abs(raw_value - self.current_ema) > self.max_jump:
                self.consecutive_jumps += 1
                if self.consecutive_jumps < 5:
                    return self.current_ema
            else:
                self.consecutive_jumps = 0

        # B. Median filter
        self.raw_buffer.append(raw_value)
        if len(self.raw_buffer) > self.median_window_size:
            self.raw_buffer.pop(0)
        median_value = float(np.median(self.raw_buffer))

        # C. EMA
        if self.current_ema is None:
            self.current_ema = median_value
        else:
            self.current_ema = (
                self.ema_alpha * median_value
                + (1 - self.ema_alpha) * self.current_ema
            )

        return self.current_ema
