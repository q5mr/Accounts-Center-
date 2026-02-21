import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

app_flask = Flask(__name__)

telegram_app = ApplicationBuilder().token(TOKEN).build()

# ================= HANDLER =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Bot is running on Railway Webhook!")

telegram_app.add_handler(CommandHandler("start", start))

# ================= WEBHOOK ROUTE =================
@app_flask.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"

@app_flask.route("/")
def home():
    return "Bot is alive"

# ================= START =================
if __name__ == "__main__":
    telegram_app.bot.set_webhook(
        url=f"{os.getenv('RAILWAY_STATIC_URL')}/{TOKEN}"
    )
    app_flask.run(host="0.0.0.0", port=PORT)
