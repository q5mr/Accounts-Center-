import os
import json
import random
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI")
ADMIN_ID = 6808384195
BOT_USERNAME = "@q5mww"

DATA_FILE = "data.json"

# ---------------- DATABASE ----------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

def ensure_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "points": 0,
            "daily": "",
            "invites": 0
        }

    if int(uid) == ADMIN_ID:
        data["users"][uid]["points"] = 9999

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)
    save_data()

    text = f"""
✨ Welcome to Premium Store Bot ✨
حقوق: {BOT_USERNAME}

💰 Points: {data["users"][str(user.id)]["points"]}
"""

    keyboard = [
        [InlineKeyboardButton("🎁 Daily Gift", callback_data="daily")],
        [InlineKeyboardButton("🎰 Spin Wheel (2 pts)", callback_data="wheel")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leader")],
        [InlineKeyboardButton("🛠 Support", url="https://t.me/netflix_centerBOT")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- CALLBACK ----------------

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    ensure_user(user_id)

    uid = str(user_id)

    # Daily
    if query.data == "daily":
        today = str(datetime.now().date())

        if data["users"][uid]["daily"] == today:
            await query.edit_message_text("❌ You already claimed today.")
        else:
            data["users"][uid]["daily"] = today
            data["users"][uid]["points"] += 1
            save_data()
            await query.edit_message_text("🎁 You received 1 point!")

    # Wheel
    elif query.data == "wheel":
        if data["users"][uid]["points"] < 2:
            await query.edit_message_text("❌ Not enough points.")
        else:
            data["users"][uid]["points"] -= 2
            reward = random.choice([0,1,2,3,5])
            data["users"][uid]["points"] += reward
            save_data()
            await query.edit_message_text(f"🎰 You won {reward} points!")

    # Leaderboard
    elif query.data == "leader":
        sorted_users = sorted(
            data["users"].items(),
            key=lambda x: x[1]["points"],
            reverse=True
        )[:10]

        text = "🏆 Top Users\n\n"
        for i, (u, info) in enumerate(sorted_users, 1):
            text += f"{i}. {info['points']} pts\n"

        await query.edit_message_text(text)

# ---------------- ADMIN ----------------

async def addpoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = context.args[0]
        amount = int(context.args[1])
        ensure_user(user_id)
        data["users"][str(user_id)]["points"] += amount
        save_data()
        await update.message.reply_text("✅ Points added.")
    except:
        await update.message.reply_text("Usage: /addpoints user_id amount")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    for u in data["users"]:
        try:
            await context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    await update.message.reply_text("📢 Broadcast sent.")

# ---------------- COMMANDS MENU ----------------

async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📜 Available Commands

/start - Start bot
/commands - Show commands

👑 Admin Only:
/addpoints user_id amount
/broadcast message
"""
    await update.message.reply_text(text)

# ---------------- RUN ----------------

async def set_bot_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start bot"),
        BotCommand("commands", "Show commands")
    ])

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("commands", commands))
app.add_handler(CommandHandler("addpoints", addpoints))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CallbackQueryHandler(button))

app.post_init = set_bot_commands

print("Bot Running...")

app.run_polling()

