import asyncio
import datetime
import logging
import config
from deriv_client import DerivClient
from ai_engine import AIEngine
from risk_manager import RiskManager
from telegram_bot import TelegramInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DerivAIBot:
    def __init__(self):
        self.deriv = DerivClient()
        self.ai = AIEngine()
        self.risk = RiskManager()
        self.tg = TelegramInterface(self)
        self.candles = []
        self.state = {
            "running": False,
            "ai_mode": config.AI_MODE,
            "symbol": config.ACTIVE_SYMBOL,
            "balance": 0.0,
            "daily_pnl": 0.0,
            "last_signal": "WAIT",
            "last_confidence": 0.0
        }

    async def start(self):
        try:
            await self.deriv.connect()
            self.state['balance'] = self.deriv.balance
            self.risk.set_balance(self.deriv.balance)
            await self.tg.app.bot.send_message(
                config.CHAT_ID,
                f"🤖 *DERIV AI BOT DÉMARRÉ*\n"
                f"💰 Solde : {self.deriv.balance:.2f} USD\n"
                f"🧠 Mode : {config.AI_MODE}\n"
                f"💹 Symbole : {config.ACTIVE_SYMBOL}\n"
                f"Envoie /start pour le menu !",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Erreur connexion Deriv: {e}")

        await self.tg.app.run_polling(drop_pending_updates=True)

    async def trading_loop(self):
        while True:
            try:
                if self.state['running']:
                    await self.run_cycle()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Erreur trading loop: {e}")
                await asyncio.sleep(30)

    async def run_cycle(self):
        symbols_map = {
            "V10": "R_10", "V25": "R_25", "V50": "R_50",
            "V75": "R_75", "V100": "R_100",
            "BOOM500": "BOOM500", "CRASH500": "CRASH500",
            "STEP": "stpRNG"
        }
        symbol = self.state['symbol']
        deriv_symbol = symbols_map.get(symbol, "R_75")
        try:
            self.candles = await self.deriv.get_candles(
                deriv_symbol, count=200, tf=config.CANDLE_TF
            )
            if not self.candles:
                return
            latest_price = float(self.candles[-1]['close'])
            result = self.ai.analyze(self.candles, latest_price)
            self.state['last_signal'] = result['signal']
            self.state['last_confidence'] = result['confidence']
            self.state['ai_mode'] = result['mode']
            if result['signal'] == "WAIT":
                return
            can, reason = self.risk.can_trade(result['confidence'])
            if not can:
                return
            balance = await self.deriv.get_balance()
            self.state['balance'] = balance
            stake = self.risk.calc_stake(balance)
            trade_info = {
                "type": result['signal'],
                "symbol": symbol,
                "mode": result['mode'],
                "stake": stake,
                "confidence": result['confidence'],
                "reason": result['reason'],
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "won": None
            }
            await self.tg.send_alert(trade_info)
            buy_result = await self.deriv.buy_contract(
                result['signal'], stake,
                config.DURATION, deriv_symbol
            )
            if buy_result:
                won = float(buy_result.get('profit', 0)) > 0
                pnl = float(buy_result.get('profit', 0))
                self.risk.record_trade(won, pnl)
                self.state['daily_pnl'] += pnl
                trade_info['won'] = won
                trade_info['pnl'] = pnl
                await self.tg.send_alert(trade_info)
        except Exception as e:
            logger.error(f"Erreur run_cycle: {e}")

def main():
    bot = DerivAIBot()
    asyncio.run(bot.start())

if __name__ == "__main__":
    main()
