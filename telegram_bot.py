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
        self.app.add_handler(CommandHandler("resume", self.cmd_resume))
        self.app.add_handler(CommandHandler("balance", self.cmd_balance))
        self.app.add_handler(CommandHandler("pnl", self.cmd_pnl))
        self.app.add_handler(CommandHandler("mode", self.cmd_mode))
        self.app.add_handler(CommandHandler("symbol", self.cmd_symbol))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    def _auth(self, update):
        return str(update.effective_chat.id) == str(config.CHAT_ID)

    def _main_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("▶️ Démarrer", callback_data="start_bot"),
             InlineKeyboardButton("⏸ Pause", callback_data="pause_bot")],
            [InlineKeyboardButton("⏹ Stop", callback_data="stop_bot"),
             InlineKeyboardButton("📊 Statut", callback_data="status")],
            [InlineKeyboardButton("💰 Solde", callback_data="balance"),
             InlineKeyboardButton("📈 PnL", callback_data="pnl")],
            [InlineKeyboardButton("🌊 TREND", callback_data="mode_TREND"),
             InlineKeyboardButton("⚡ SCALP", callback_data="mode_SCALP"),
             InlineKeyboardButton("🔄 SWING", callback_data="mode_SWING"),
             InlineKeyboardButton("🤖 AUTO", callback_data="mode_AUTO")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if self.bot_engine:
            self.bot_engine.state['running'] = True
        await update.message.reply_text(
            "🤖 *DERIV AI TRADING BOT*\n"
            "━━━━━━━━━━━━━━━\n"
            "✅ Bot démarré !\n"
            f"💹 Symbole : {config.ACTIVE_SYMBOL}\n"
            f"🧠 Mode : {config.AI_MODE}\n"
            "━━━━━━━━━━━━━━━\n"
            "Choisis une action :",
            parse_mode="Markdown",
            reply_markup=self._main_keyboard()
        )

    async def cmd_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if self.bot_engine:
            s = self.bot_engine.state
            msg = (
                "📊 *STATUT DU BOT*\n"
                "━━━━━━━━━━━━━━━\n"
                f"▶️ Actif : {'✅ Oui' if s['running'] else '❌ Non'}\n"
                f"💰 Solde : {s['balance']:.2f} USD\n"
                f"📈 PnL du jour : {s['daily_pnl']:+.2f} USD\n"
                f"🎯 Dernier signal : {s['last_signal']}\n"
                f"🔥 Confiance : {s['last_confidence']:.1%}\n"
                f"💹 Symbole : {s['symbol']}\n"
                f"🧠 Mode IA : {s['ai_mode']}"
            )
        else:
            msg = "📊 Bot actif."
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    msg, parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
            except Exception as e:
                logger.warning(f"Status edit warning: {e}")
        else:
            await update.message.reply_text(
                msg, parse_mode="Markdown",
                reply_markup=self._main_keyboard()
            )

    async def cmd_stop(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if self.bot_engine:
            self.bot_engine.state['running'] = False
        await update.message.reply_text(
            "⏹ *Bot arrêté.*",
            parse_mode="Markdown",
            reply_markup=self._main_keyboard()
        )

    async def cmd_pause(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if self.bot_engine:
            self.bot_engine.state['running'] = False
        await update.message.reply_text(
            "⏸ *Bot en pause.*",
            parse_mode="Markdown",
            reply_markup=self._main_keyboard()
        )

    async def cmd_resume(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if self.bot_engine:
            self.bot_engine.state['running'] = True
        await update.message.reply_text(
            "▶️ *Bot repris !*",
            parse_mode="Markdown",
            reply_markup=self._main_keyboard()
        )

    async def cmd_balance(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        bal = self.bot_engine.state['balance'] if self.bot_engine else 0
        await update.message.reply_text(
            f"💰 *Solde : {bal:.2f} USD*",
            parse_mode="Markdown"
        )

    async def cmd_pnl(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        pnl = self.bot_engine.state['daily_pnl'] if self.bot_engine else 0
        await update.message.reply_text(
            f"📈 *PnL aujourd'hui : {pnl:+.2f} USD*",
            parse_mode="Markdown"
        )

    async def cmd_mode(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if ctx.args and self.bot_engine:
            mode = ctx.args[0].upper()
            if mode in ["AUTO", "TREND", "SCALP", "SWING"]:
                self.bot_engine.ai.mode = mode
                self.bot_engine.state['ai_mode'] = mode
                await update.message.reply_text(
                    f"🧠 *Mode changé : {mode}*",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "❌ Mode invalide. Choisis : AUTO, TREND, SCALP, SWING"
                )
        else:
            await update.message.reply_text(
                "Usage : /mode AUTO"
            )

    async def cmd_symbol(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        if ctx.args and self.bot_engine:
            self.bot_engine.state['symbol'] = ctx.args[0].upper()
            await update.message.reply_text(
                f"💹 *Symbole changé : {ctx.args[0].upper()}*",
                parse_mode="Markdown"
            )

    async def cmd_help(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._auth(update):
            return
        msg = (
            "📋 *COMMANDES DISPONIBLES*\n"
            "━━━━━━━━━━━━━━━\n"
            "/start — Démarrer le bot\n"
            "/stop — Arrêter le bot\n"
            "/pause — Mettre en pause\n"
            "/resume — Reprendre\n"
            "/status — État du bot\n"
            "/balance — Voir le solde\n"
            "/pnl — Profit et perte\n"
            "/mode AUTO — Changer le mode\n"
            "/symbol V75 — Changer l'indice\n"
            "/help — Cette liste"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def handle_callback(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if not self._auth(update):
            return
        try:
            if query.data == "start_bot":
                if self.bot_engine:
                    self.bot_engine.state['running'] = True
                await query.edit_message_text(
                    "▶️ *Bot démarré !*",
                    parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
            elif query.data == "stop_bot":
                if self.bot_engine:
                    self.bot_engine.state['running'] = False
                await query.edit_message_text(
                    "⏹ *Bot arrêté.*",
                    parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
            elif query.data == "pause_bot":
                if self.bot_engine:
                    self.bot_engine.state['running'] = False
                await query.edit_message_text(
                    "⏸ *Bot en pause.*",
                    parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
            elif query.data == "status":
                await self.cmd_status(update, ctx)
            elif query.data == "balance":
                bal = self.bot_engine.state['balance'] if self.bot_engine else 0
                await query.edit_message_text(
                    f"💰 *Solde : {bal:.2f} USD*",
                    parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
            elif query.data == "pnl":
                pnl = self.bot_engine.state['daily_pnl'] if self.bot_engine else 0
                await query.edit_message_text(
                    f"📈 *PnL : {pnl:+.2f} USD*",
                    parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
            elif query.data.startswith("mode_"):
                mode = query.data.split("_")[1]
                if self.bot_engine:
                    self.bot_engine.ai.mode = mode
                    self.bot_engine.state['ai_mode'] = mode
                await query.edit_message_text(
                    f"🧠 *Mode changé : {mode}*",
                    parse_mode="Markdown",
                    reply_markup=self._main_keyboard()
                )
        except Exception as e:
            logger.warning(f"Callback warning: {e}")

    async def send_alert(self, trade_info: dict):
        try:
            if trade_info.get('won') is None:
                emoji = "🔔"
                msg = (
                    f"{emoji} *SIGNAL {trade_info['type']}*\n"
                    f"💹 {trade_info['symbol']} | 🧠 {trade_info['mode']}\n"
                    f"💵 Mise : {trade_info['stake']:.2f} USD\n"
                    f"🔥 Confiance : {trade_info['confidence']:.1%}\n"
                    f"📝 {trade_info['reason']}\n"
                    f"🕐 {trade_info['time']}"
                )
            else:
                emoji = "✅" if trade_info['won'] else "❌"
                msg = (
                    f"{emoji} *RÉSULTAT*\n"
                    f"💹 {trade_info['symbol']} | {trade_info['type']}\n"
                    f"💰 PnL : {trade_info.get('pnl', 0):+.2f} USD\n"
                    f"🕐 {trade_info['time']}"
                )
            await self.app.bot.send_message(
                chat_id=config.CHAT_ID,
                text=msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Erreur send_alert: {e}")
