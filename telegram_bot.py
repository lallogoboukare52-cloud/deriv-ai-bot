import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramInterface:
    def __init__(self, token: str, chat_id: str, bot_engine=None):
        self.token = token
        self.chat_id = str(chat_id)
        self.bot_engine = bot_engine
        self.app = Application.builder().token(token).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("stop", self.cmd_stop))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    async def cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("▶️ Démarrer", callback_data="start_bot"),
             InlineKeyboardButton("⏹ Stop", callback_data="stop_bot")],
            [InlineKeyboardButton("📊 Statut", callback_data="status")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🤖 *Deriv AI Trading Bot*\nChoisissez une action :",
            parse_mode="Markdown",
            reply_markup=markup
        )

    async def cmd_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📊 Bot actif et en cours d'exécution.")

    async def cmd_stop(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏹ Arrêt du bot...")

    async def handle_callback(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == "start_bot":
            await query.edit_message_text("▶️ Bot démarré !")
        elif query.data == "stop_bot":
            await query.edit_message_text("⏹ Bot arrêté.")
        elif query.data == "status":
            await query.edit_message_text("📊 Bot actif.")

    async def send_message(self, text: str):
        async with self.app.bot:
            await self.app.bot.send_message(chat_id=self.chat_id, text=text)

    def run(self):
        logger.info("Démarrage du bot Telegram...")
        self.app.run_polling()
