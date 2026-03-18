import numpy as np

class SRDetector:
    def __init__(self, sensitivity=0.001):
        self.levels = []
        self.sensitivity = sensitivity

    def detect_levels(self, highs, lows, closes):
        levels = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                levels.append({'price': highs[i], 'type': 'resistance', 'touches': 1})
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                levels.append({'price': lows[i], 'type': 'support', 'touches': 1})
        self.levels = self._cluster_levels(levels, closes[-1])
        return self.levels

    def _cluster_levels(self, levels, current_price):
        clustered = []
        for lvl in levels:
            merged = False
            for c in clustered:
                if abs(c['price'] - lvl['price']) / current_price < self.sensitivity:
                    c['touches'] += 1
                    c['price'] = (c['price'] + lvl['price']) / 2
                    merged = True
                    break
            if not merged:
                clustered.append(lvl.copy())
        return [l for l in clustered if l['touches'] >= 2]

    def nearest_levels(self, price, n=3):
        sorted_lvls = sorted(self.levels, key=lambda x: abs(x['price'] - price))
        return sorted_lvls[:n]

    def is_near_level(self, price, threshold=0.002):
        for lvl in self.levels:
            dist = abs(lvl['price'] - price) / price
            if dist < threshold:
                return {'near': True, 'level': lvl, 'distance_pct': dist * 100}
        return {'near': False}