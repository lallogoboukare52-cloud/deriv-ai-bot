import numpy as np
from collections import deque

class OrderBookAnalyzer:
    def __init__(self, window=50):
        self.ticks = deque(maxlen=window)
        self.tick_directions = deque(maxlen=window)

    def add_tick(self, price):
        if len(self.ticks) > 0:
            prev = self.ticks[-1]
            if price > prev:
                self.tick_directions.append(1)
            elif price < prev:
                self.tick_directions.append(-1)
            else:
                self.tick_directions.append(0)
        self.ticks.append(price)

    def get_obi(self):
        if len(self.tick_directions) < 10:
            return 0.0
        dirs = np.array(self.tick_directions)
        buys = np.sum(dirs > 0)
        sells = np.sum(dirs < 0)
        total = buys + sells
        if total == 0:
            return 0.0
        return (buys - sells) / total

    def get_signal(self):
        obi = self.get_obi()
        if obi > 0.55:
            return "CALL"
        elif obi < -0.55:
            return "PUT"
        return "NEUTRAL"

    def get_momentum(self, n=10):
        if len(self.ticks) < n:
            return 0.0
        recent = list(self.ticks)[-n:]
        return (recent[-1] - recent[0]) / recent[0] * 100