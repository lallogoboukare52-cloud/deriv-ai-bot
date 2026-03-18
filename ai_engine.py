import pandas as pd
import pandas_ta as ta
import numpy as np
from order_book import OrderBookAnalyzer
from sr_detector import SRDetector
import config

class AIEngine:
    def __init__(self):
        self.ob = OrderBookAnalyzer(window=100)
        self.sr = SRDetector(sensitivity=0.001)
        self.mode = config.AI_MODE

    def detect_regime(self, df):
        adx_df = ta.adx(df['high'], df['low'], df['close'])
        adx = adx_df['ADX_14'].iloc[-1]
        atr = ta.atr(df['high'], df['low'], df['close']).iloc[-1]
        avg_atr = ta.atr(df['high'], df['low'], df['close']).mean()
        if adx > 25:
            return "TREND"
        elif atr > avg_atr * 1.5:
            return "SCALP"
        else:
            return "SWING"

    def analyze(self, candles, latest_tick):
        if len(candles) < 50:
            return {"signal": "WAIT", "confidence": 0, "mode": "LOADING", "reason": "Chargement"}
        df = pd.DataFrame(candles)
        df.columns = ['epoch', 'open', 'high', 'low', 'close']
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col])
        self.ob.add_tick(latest_tick)
        self.sr.detect_levels(df['high'].values, df['low'].values, df['close'].values)
        active_mode = self.detect_regime(df) if self.mode == "AUTO" else self.mode
        if active_mode == "TREND":
            return self._trend_signal(df, latest_tick)
        elif active_mode == "SCALP":
            return self._scalp_signal(df, latest_tick)
        else:
            return self._swing_signal(df, latest_tick)

    def _trend_signal(self, df, price):
        ema9 = ta.ema(df['close'], length=9).iloc[-1]
        ema21 = ta.ema(df['close'], length=21).iloc[-1]
        ema50 = ta.ema(df['close'], length=50).iloc[-1]
        adx_df = ta.adx(df['high'], df['low'], df['close'])
        adx = adx_df['ADX_14'].iloc[-1]
        dip = adx_df['DMP_14'].iloc[-1]
        dim = adx_df['DMN_14'].iloc[-1]
        macd_df = ta.macd(df['close'])
        macd = macd_df['MACD_12_26_9'].iloc[-1]
        sig = macd_df['MACDs_12_26_9'].iloc[-1]
        score = 0
        if ema9 > ema21 > ema50: score += 0.3
        if adx > 25: score += 0.2
        if dip > dim: score += 0.2
        if macd > sig: score += 0.15
        if price > ema9: score += 0.15
        if score >= config.MIN_CONFIDENCE:
            return {"signal": "CALL", "confidence": score, "mode": "TREND", "reason": "EMA+ADX+MACD haussier"}
        score2 = 0
        if ema9 < ema21 < ema50: score2 += 0.3
        if adx > 25: score2 += 0.2
        if dim > dip: score2 += 0.2
        if macd < sig: score2 += 0.15
        if price < ema9: score2 += 0.15
        if score2 >= config.MIN_CONFIDENCE:
            return {"signal": "PUT", "confidence": score2, "mode": "TREND", "reason": "EMA+ADX+MACD baissier"}
        return {"signal": "WAIT", "confidence": 0, "mode": "TREND", "reason": "Pas de signal"}

    def _scalp_signal(self, df, price):
        rsi = ta.rsi(df['close'], length=7).iloc[-1]
        obi = self.ob.get_obi()
        mom = self.ob.get_momentum(5)
        bb = ta.bbands(df['close'], length=10)
        bbl = bb['BBL_10_2.0'].iloc[-1]
        bbu = bb['BBU_10_2.0'].iloc[-1]
        score_c = 0
        score_p = 0
        if obi > config.OBI_THRESHOLD: score_c += 0.4
        if rsi < 35: score_c += 0.3
        if mom > 0: score_c += 0.15
        if price <= bbl: score_c += 0.15
        if obi < -config.OBI_THRESHOLD: score_p += 0.4
        if rsi > 65: score_p += 0.3
        if mom < 0: score_p += 0.15
        if price >= bbu: score_p += 0.15
        if score_c >= config.MIN_CONFIDENCE:
            return {"signal": "CALL", "confidence": score_c, "mode": "SCALP", "reason": "OBI+RSI+BB haussier"}
        if score_p >= config.MIN_CONFIDENCE:
            return {"signal": "PUT", "confidence": score_p, "mode": "SCALP", "reason": "OBI+RSI+BB baissier"}
        return {"signal": "WAIT", "confidence": 0, "mode": "SCALP", "reason": "Pas de signal"}

    def _swing_signal(self, df, price):
        rsi = ta.rsi(df['close'], length=14).iloc[-1]
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        sk = stoch['STOCHk_14_3_3'].iloc[-1]
        sr_info = self.sr.is_near_level(price)
        ema200 = ta.ema(df['close'], length=200).iloc[-1]
        score_c = 0
        score_p = 0
        if rsi < 30: score_c += 0.35
        if sk < 20: score_c += 0.25
        if price > ema200: score_c += 0.2
        if sr_info['near'] and sr_info.get('level', {}).get('type') == 'support':
            score_c += 0.2
        if rsi > 70: score_p += 0.35
        if sk > 80: score_p += 0.25
        if price < ema200: score_p += 0.2
        if sr_info['near'] and sr_info.get('level', {}).get('type') == 'resistance':
            score_p += 0.2
        if score_c >= config.MIN_CONFIDENCE:
            return {"signal": "CALL", "confidence": score_c, "mode": "SWING", "reason": "RSI+Stoch+SR haussier"}
        if score_p >= config.MIN_CONFIDENCE:
            return {"signal": "PUT", "confidence": score_p, "mode": "SWING", "reason": "RSI+Stoch+SR baissier"}
        return {"signal": "WAIT", "confidence": 0, "mode": "SWING", "reason": "Pas de signal"}