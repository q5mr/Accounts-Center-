import json, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"

ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
CONTACT_USERNAME = "@q5mww"

POINT_COST = 3


PLATFORMS = {
    "Netflix": "🔴",
    "Prime": "🔵",
    "Disney+": "🟦",
    "Hulu": "🟢",
    "HBO": "🟣",
    "Crunchyroll": "🟠",
    "Spotify": "🟢",
    "Steam": "⚙️",
    "Xbox": "🟩",
    "PSN": "🔷",
}

REQUIRED_CHANNELS = [
    ("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free"),
    ("@freebroorsell", "https://t.me/freebroorsell")
]


# ================= DATABASE =================

def load_users():
    if not os.path.exists("users.json"):
        return {}
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f)

users = load_users()


# ================= STOCK SYSTEM =================

def deliver_account(platform):
    file_name = f"{platform}.txt"

    if not os.path.exists(file_name):
        return None

    with open(file_name, "r") as f:
        lines = f.readlines()

    if not lines:
        return None

    account = lines[0].strip()

    with open(file_name, "w") as f:
        f.writelines(lines[1:])

    return account


# ================= MEMBERSHIP =================

async def is_member(bot, user_id):
    for ch, _ in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "points": 999999 if user.id == ADMIN_ID else 0,
            "ref_by": None,
            "invited": []
        }

    save_users(users)

    if not await is_member(context.bot, user.id):

        buttons = []
        for _, link in REQUIRED_CHANNELS:
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=link)])

        await update.message.reply_text(
            "🚨 Please join required channels first.\n\nAfter subscribing press /start again.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await main_menu(update, context)


# ================= MAIN MENU =================

async def main_menu(update, context):

    user = update.effective_user
    user_id = str(user.id)
    points = users[user_id]["points"]

    buttons = []
    row = []

    for name, emoji in PLATFORMS.items():
        row.append(InlineKeyboardButton(f"{emoji} {name}", callback_data=f"p_{name}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    text = (
        "✨ DIGITAL STORE ✨\n\n"
        f"👋 {user.first_name}\n"
        f"🎯 Points: {points}\n\n"
        "Select Platform"
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ================= PLATFORM =================

async def choose_platform(update: Update, context):
    q = update.callback_query
    await q.answer()

    platform = q.data[2:]
    context.user_data["platform"] = platform

    buttons = [
        [
            InlineKeyboardButton("💳 Buy", callback_data="buy"),
            InlineKeyboardButton("🎁 Free", callback_data="free")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]

    await q.edit_message_text(
        f"🎬 {platform}\n\nChoose option:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ================= ACTION =================

async def action(update: Update, context):
    q = update.callback_query
    await q.answer()

    user_id = str(q.from_user.id)

    if q.data == "back":
        await main_menu(update, context)
        return

    if q.data == "buy":
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back_platform")]]
        await q.edit_message_text(
            "💳 Payment Methods\n\n"
            "Binance ID: 791001890\n"
            "PayPal: raoufeboukhamla18@gmail.com\n\n"
            f"📩 Contact: {CONTACT_USERNAME}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if q.data == "back_platform":
        await choose_platform(update, context)
        return

    if q.data == "free":

        platform = context.user_data.get("platform")
        if not platform:
            await q.edit_message_text("Session expired. Press /start again.")
            return

        if users[user_id]["points"] < POINT_COST:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await q.edit_message_text(
                f"❌ Not enough points\n\nInvite friends:\n{ref_link}"
            )
            return

        account = deliver_account(platform)

        if not account:
            await q.edit_message_text("⚠ Out of Stock")
            await context.bot.send_message(LOG_CHANNEL, f"{platform} Out of Stock")
            return

        users[user_id]["points"] -= POINT_COST
        save_users(users)

        await q.edit_message_text(
            f"✅ Delivered:\n\n{account}"
        )

        await context.bot.send_message(
            LOG_CHANNEL,
            f"New Delivery\nUser: {user_id}\nPlatform: {platform}\nAccount: {account}"
        )


# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_platform, pattern="^p_"))
app.add_handler(CallbackQueryHandler(action, pattern="^(buy|free|back|back_platform)$"))

app.run_polling()
