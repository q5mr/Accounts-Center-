from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ====== SETTINGS ======
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"
ADMIN_ID = 6808384195
BOT_USERNAME = "@q5mww"

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 About Bot", callback_data="about")],
        [InlineKeyboardButton("🛠 Support", url="https://t.me/netflix_centerBOT")]
    ]

    text = f"""
✨ Welcome to Premium Bot ✨

Official Rights: {BOT_USERNAME}

Use /commands to see available commands.
"""

    await update.message.reply_text(
        text.strip(),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== BUTTONS ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text(
            f"""
🤖 Premium Service Bot

👑 Owner: {BOT_USERNAME}
🛠 Admin ID: {ADMIN_ID}

Fully running from script only.
"""
        )

# ====== ADMIN COMMAND ======
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin.")
        return

    await update.message.reply_text("👑 Admin access confirmed.")

# ====== COMMANDS LIST ======
async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📜 Available Commands

/start - Start the bot
/commands - Show commands
/admin - Check admin status
"""
    await update.message.reply_text(text.strip())

# ====== REGISTER BOT COMMANDS ======
async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start bot"),
        BotCommand("commands", "Show commands"),
        BotCommand("admin", "Admin check")
    ])

# ====== RUN ======
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("commands", commands))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(buttons))

app.post_init = set_commands

print("Bot is running...")

app.run_polling()
