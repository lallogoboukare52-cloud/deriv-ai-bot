import config
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

class TelegramInterface:
    def __init__(self, bot_core):
        self.core = bot_core
        self.app = Application.builder().token(config.TELEGRAM_TOKEN).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("run", self.run))
        self.app.add_handler(CommandHandler("stop", self.stop))
        self.app.add_handler(CommandHandler("pause", self.pause))
        self.app.add_handler(CommandHandler("resume", self.resume))
        self.app.add_handler(CommandHandler("balance", self.balance))
        self.app.add_handler(CommandHandler("pnl", self.pnl))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(CommandHandler("mode", self.set_mode))
        self.app.add_handler(CommandHandler("symbol", self.set_symbol))
        self.app.add_handler(CommandHandler("risk", self.set_risk))
        self.app.add_handler(CommandHandler("levels", self.sr_levels))
        self.app.add_handler(CommandHandler("help", self.help_cmd))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    def _auth(self, update):
        return str(update.effective_chat.id) == str(config.CHAT_ID)

    async def start(self, update, ctx):
        if not self._auth(update): return
        kb = [
            [InlineKeyboardButton("▶️ START", callback_data="run"),
             InlineKeyboardButton("⏹ STOP", callback_data="stop"),
             InlineKeyboardButton("📊 STATUS", callback_data="status")],
            [InlineKeyboardButton("🌊 TREND", callback_data="mode_TREND"),
             InlineKeyboardButton("⚡ SCALP", callback_data="mode_SCALP"),
             InlineKeyboardButton("🔄 SWING", callback_data="mode_SWING"),
             InlineKeyboardButton("🤖 AUTO", callback_data="mode_AUTO")],
            [InlineKeyboardButton("💰 SOLDE", callback_data="balance"),
             InlineKeyboardButton("📈 PNL", callback_data="pnl"),
             InlineKeyboardButton("📊 STATS", callback_data="stats")],
            [InlineKeyboardButton("📍 SR", callback_data="levels"),
             InlineKeyboardButton("⏸ PAUSE", callback_data="pause"),
             InlineKeyboardButton("▶️ RESUME", callback_data="resume")]
        ]
        await update.message.reply_text(
            "🤖 *DERIV AI TRADING BOT*\nChoisis une action :",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )

    async def status(self, update, ctx):
        if not self._auth(update): return
        s = self.core.state
        rm = self.core.risk.get_stats()
        now = datetime.datetime.now().strftime("%H:%M:%S")
        msg = f"""
🤖 *DERIV AI BOT STATUS*
━━━━━━━━━━━━━━━━
🟢 Actif : {s['running']}
🧠 Mode : {s['ai_mode']}
💹 Symbole : {s['symbol']}
💰 Solde : {s['balance']:.2f} USD
📊 PnL jour : {s['daily_pnl']:+.2f} USD
📈 Trades : {rm['daily_trades']}/{config.MAX_DAILY_TRADES}
❌ Pertes : {rm['daily_loss_pct']:.1f}%
🎯 Signal : {s['last_signal']}
⏰ Heure : {now}
        """
        if update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")

    async def run(self, update, ctx):
        if not self._auth(update): return
        self.core.state['running'] = True
        msg = "▶️ *Bot démarré !*\nAnalyse du marché en cours..."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")

    async def stop(self, update, ctx):
        if not self._auth(update): return
        self.core.state['running'] = False
        msg = "⏹ *Bot arrêté.*"
        if update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")

    async def pause(self, update, ctx):
        if not self._auth(update): return
        self.core.state['running'] = False
        await update.message.reply_text("⏸ *Bot en pause.*", parse_mode="Markdown")

    async def resume(self, update, ctx):
        if not self._auth(update): return
        self.core.state['running'] = True
        await update.message.reply_text("▶️ *Bot repris.*", parse_mode="Markdown")

    async def balance(self, update, ctx):
        if not self._auth(update): return
        bal = self.core.state['balance']
        await update.message.reply_text(f"💰 *Solde : {bal:.2f} USD*", parse_mode="Markdown")

    async def pnl(self, update, ctx):
        if not self._auth(update): return
        pnl = self.core.state['daily_pnl']
        await update.message.reply_text(f"📈 *PnL aujourd'hui : {pnl:+.2f} USD*", parse_mode="Markdown")

    async def stats(self, update, ctx):
        if not self._auth(update): return
        rm = self.core.risk.get_stats()
        msg = f"""
📊 *STATISTIQUES*
━━━━━━━━━━━━
Trades aujourd'hui : {rm['daily_trades']}
Pertes journalières : {rm['daily_loss_pct']:.1f}%
Pertes consécutives : {rm['consecutive_loss']}
Pause active : {rm['paused']}
        """
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def set_mode(self, update, ctx):
        if not self._auth(update): return
        if ctx.args:
            mode = ctx.args[0].upper()
            if mode in ["AUTO", "TREND", "SCALP", "SWING"]:
                self.core.ai.mode = mode
                self.core.state['ai_mode'] = mode
                await update.message.reply_text(f"🧠 *Mode changé : {mode}*", parse_mode="Markdown")

    async def set_symbol(self, update, ctx):
        if not self._auth(update): return
        if ctx.args:
            self.core.state['symbol'] = ctx.args[0].upper()
            await update.message.reply_text(f"💹 *Symbole : {ctx.args[0].upper()}*", parse_mode="Markdown")

    async def set_risk(self, update, ctx):
        if not self._auth(update): return
        if ctx.args:
            risk = float(ctx.args[0]) / 100
            config.RISK_PER_TRADE = risk
            await update.message.reply_text(f"⚠️ *Risque/trade : {ctx.args[0]}%*", parse_mode="Markdown")

    async def sr_levels(self, update, ctx):
        if not self._auth(update): return
        levels = self.core.ai.sr.levels[:5]
        if not levels:
            await update.message.reply_text("📍 Pas encore de niveaux détectés.")
            return
        msg = "📍 *SUPPORTS / RÉSISTANCES*\n━━━━━━━━━━━━\n"
        for l in levels:
            emoji = "🟢" if l['type'] == 'support' else "🔴"
            msg += f"{emoji} {l['type'].upper()} : {l['price']:.4f} ({l['touches']} touches)\n"
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def help_cmd(self, update, ctx):
        if not self._auth(update): return
        msg = """
📋 *COMMANDES DISPONIBLES*
━━━━━━━━━━━━━━
/start — Menu principal
/status — État du bot
/run — Démarrer
/stop — Arrêter
/pause — Pause
/resume — Reprendre
/balance — Solde
/pnl — Profit et perte
/stats — Statistiques
/mode AUTO — Changer mode
/symbol V75 — Changer indice
/risk 2 — Risque en %
/levels — Supports/Résistances
/help — Cette liste
        """
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def handle_callback(self, update, ctx):
        if not self._auth(update): return
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == "run":
            await self.run(update, ctx)
        elif data == "stop":
            await self.stop(update, ctx)
        elif data == "status":
            await self.status(update, ctx)
        elif data == "balance":
            await self.balance(update, ctx)
        elif data == "pnl":
            await self.pnl(update, ctx)
        elif data == "stats":
            await self.stats(update, ctx)
        elif data == "levels":
            await self.sr_levels(update, ctx)
        elif data == "pause":
            await self.pause(update, ctx)
        elif data == "resume":
            await self.resume(update, ctx)
        elif data.startswith("mode_"):
            mode = data.split("_")[1]
            self.core.ai.mode = mode
            self.core.state['ai_mode'] = mode
            await query.edit_message_text(f"🧠 *Mode changé : {mode}*", parse_mode="Markdown")

    async def send_alert(self, trade):
        e = "🟢" if trade['type'] == "CALL" else "🔴"
        won = trade.get('won')
        result = "✅ GAGNE" if won else "❌ PERDU" if won is not None else "⏳ EN COURS"
        msg = f"""
{e} *TRADE {trade['type']}* {result}
━━━━━━━━━━━━
💹 {trade['symbol']} | {trade['mode']}
💵 Mise : {trade['stake']} USD
🎯 Confiance : {trade['confidence']:.0%}
📝 {trade['reason']}
⏰ {trade['time']}
        """
        await self.app.bot.send_message(config.CHAT_ID, msg, parse_mode="Markdown")