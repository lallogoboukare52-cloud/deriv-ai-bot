import datetime
import config

class RiskManager:
    def __init__(self):
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.consecutive_loss = 0
        self.initial_balance = 0.0
        self.last_reset = datetime.date.today()
        self.paused = False
        self.pause_reason = ""

    def set_balance(self, bal):
        if self.initial_balance == 0:
            self.initial_balance = bal

    def _reset_daily(self):
        today = datetime.date.today()
        if today > self.last_reset:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset = today
            self.paused = False

    def can_trade(self, confidence):
        self._reset_daily()
        if self.paused:
            return False, "Pause active"
        if self.daily_trades >= config.MAX_DAILY_TRADES:
            return False, "Limite journaliere atteinte"
        if self.daily_loss >= config.MAX_DAILY_LOSS:
            return False, "Daily loss limit atteint"
        if self.consecutive_loss >= config.MAX_CONSECUTIVE_LOSS:
            self.paused = True
            self.pause_reason = "3 pertes consecutives"
            return False, "Pause apres 3 pertes"
        if confidence < config.MIN_CONFIDENCE:
            return False, "Confiance IA trop faible"
        return True, "OK"

    def calc_stake(self, balance):
        stake = balance * config.RISK_PER_TRADE
        stake = max(0.35, min(stake, config.MAX_STAKE))
        return round(stake, 2)

    def record_trade(self, won, pnl):
        self.daily_trades += 1
        if not won:
            self.daily_loss += abs(pnl) / (self.initial_balance or 1)
            self.consecutive_loss += 1
        else:
            self.consecutive_loss = 0

    def get_stats(self):
        return {
            "daily_trades": self.daily_trades,
            "daily_loss_pct": self.daily_loss * 100,
            "consecutive_loss": self.consecutive_loss,
            "paused": self.paused,
            "pause_reason": self.pause_reason
        }