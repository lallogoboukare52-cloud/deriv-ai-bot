import logging
import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramInterface:
    def __init__(self, bot_engine=None):
        self.bot_engine = bot_engine
        self.app = Application.builder().token(config.TELEGRAM_TOKEN).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("stop", self.cmd_stop))
        self.app.add_handler(CommandHandler("pause", self.cmd_pause))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    def _main_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("▶️ Démarrer", callback_data="start_bot"),
             InlineKeyboardButton("⏸ Pause", callback_data="pause_bot")],
            [InlineKeyboardButton("⏹ Stop", callback_data="stop_bot"),
             InlineKeyboardButton("📊 Statut", callback_data="status")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.bot_engine:
            self.bot_engine.state['running'] = True
        await update.message.reply_text(
            "🤖 *Deriv AI Trading Bot*\n"
            "✅ Bot démarré !\n"
            f"💹 Symbole : {config.ACTIVE_SYMBOL}\n"
            f"🧠 Mode : {config.AI_MODE}",
            parse_mode="Markdown",
            reply_markup=self._main_keyboard()
        )

    async def cmd_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.bot_engine:
            s = self.bot_engine.state
            msg = (
                f"📊 *STATUT DU BOT*\n"
                f"▶️ Actif : {'Oui' if s['running'] else 'Non'}\n"
                f"💰 Solde : {s['balance']:.2f} USD\n"
                f"📈 PnL du jour : {s['daily_pnl']:.2f} USD\n"
                f"🎯 Dernier signal : {s['last_signal']}\n"
                f"🔥 Confiance : {s['last_confidence']:.1%}\n"
                f"💹 Symbole : {s['symbol']}\n"
                f"🧠 Mode IA : {s['ai_mode']}"
            )
        else:
            msg = "📊 Bot actif."
        await update.message.reply_text(msg, parse_mode="Markdown",
                                        reply_markup=self._main_keyboard())

    async def cmd_stop(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.bot_engine:
            self.bot_engine.state['running'] = False
        await update.message.reply_text("⏹ *Bot arrêté.*",
                                        parse_mode="Markdown",
                                        reply_markup=self._main_keyboard())

    async def cmd_pause(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.bot_engine:
            self.bot_engine.state['running'] = False
        await update.message.reply_text("⏸ *Bot en pause.*",
                                        parse_mode="Markdown",
                                        reply_markup=self._main_keyboard())

    async def handle_callback(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if self.bot_engine:
            if query.data == "start_bot":
                self.bot_engine.state['running'] = True
                await query.edit_message_text("▶️ *Bot démarré !*",
                                              parse_mode="Markdown",
                                              reply_markup=self._main_keyboard())
            elif query.data == "stop_bot":
                self.bot_engine.state['running'] = False
                await query.edit_message_text("⏹ *Bot arrêté.*",
                                              parse_mode="Markdown",
                                              reply_markup=self._main_keyboard())
            elif query.data == "pause_bot":
                self.bot_engine.state['running'] = False
                await query.edit_message_text("⏸ *Bot en pause.*",
                                              parse_mode="Markdown",
                                              reply_markup=self._main_keyboard())
            elif query.data == "status":
                await self.cmd_status(update, ctx)

    async def send_alert(self, trade_info: dict):
        if trade_info.get('won') is None:
            emoji = "🔔"
            msg = (
                f"{emoji} *SIGNAL {trade_info['type']}*\n"
                f"💹 {trade_info['symbol']} | 🧠 {trade_info['mode']}\n"
                f"💵 Mise : {trade_info['stake']:.2f} USD\n"
                f"🔥 Confiance : {trade_info['confidence']:.1%}\n"
                f"📝 Raison : {trade_info['reason']}\n"
                f"🕐 {trade_info['time']}"
            )
        else:
            emoji = "✅" if trade_info['won'] else "❌"
            msg = (
                f"{emoji} *RÉSULTAT*\n"
                f"💹 {trade_info['symbol']} | {trade_info['type']}\n"
                f"💰 PnL : {trade_info.get('pnl', 0):.2f} USD\n"
                f"🕐 {trade_info['time']}"
            )
        await self.app.bot.send_message(
            chat_id=config.CHAT_ID,
            text=msg,
            parse_mode="Markdown"
    )
