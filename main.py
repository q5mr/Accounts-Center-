import json, os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
CONTACT_USERNAME = "@q5mww"
POINT_COST = 3

# Platforms must match your .txt filenames exactly (e.g., Netflix.txt)
PLATFORMS = {
    "Netflix": "🔴", "Prime": "🔵", "Disney+": "🟦", "Hulu": "🟢",
    "HBO": "🟣", "Crunchyroll": "🟠", "Spotify": "🟢", "Steam": "⚙️",
    "Xbox": "🟩", "PSN": "🔷", "HIDIVE": "🐳", "Apple TV": "🍎"
}

REQUIRED_CHANNELS = [
    ("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free"),
    ("@freebroorsell", "https://t.me/freebroorsell")
]

# --- DATABASE SYSTEM ---
def load_users():
    if not os.path.exists("users.json"): return {}
    try:
        with open("users.json", "r") as f: return json.load(f)
    except: return {}

def save_users(data):
    with open("users.json", "w") as f: json.dump(data, f, indent=4)

users = load_users()

# --- RANDOM STOCK SYSTEM ---
def deliver_account(platform):
    file_name = f"{platform}.txt"
    if not os.path.exists(file_name):
        print(f"File not found: {file_name}") # For debugging
        return None
    
    with open(file_name, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    if not lines: return None
    
    account = random.choice(lines)
    lines.remove(account)
    
    with open(file_name, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return account

# --- MEMBERSHIP CHECK ---
async def is_member(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch, _ in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in users:
        ref_id = context.args[0] if context.args else None
        users[user_id] = {"points": 999999 if user.id == ADMIN_ID else 0, "ref_by": ref_id, "invited": []}
        if ref_id and ref_id in users and ref_id != user_id:
            users[ref_id]["points"] += 1
            users[ref_id]["invited"].append(user_id)
            try: await context.bot.send_message(ref_id, "🎁 You got +1 point! New user joined via your link.")
            except: pass
        save_users(users)

    if not await is_member(context.bot, user.id):
        btns = [[InlineKeyboardButton("📢 Join Channel", url=link)] for _, link in REQUIRED_CHANNELS]
        await update.message.reply_text("🚨 Join our channels to use the bot:", reply_markup=InlineKeyboardMarkup(btns))
        return
    await main_menu(update, context)

async def main_menu(update, context):
    user_id = str(update.effective_user.id)
    pts = users.get(user_id, {}).get("points", 0)
    
    btns = []
    row = []
    for name, emoji in PLATFORMS.items():
        row.append(InlineKeyboardButton(f"{emoji} {name}", callback_data=f"p_{name}"))
        if len(row) == 3:
            btns.append(row); row = []
    if row: btns.append(row)

    text = f"✨ **DIGITAL STORE**\n\n👤 User: `{user_id}`\n🎯 Points: **{pts}**\n\nSelect Platform:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    else: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def choose_platform(update: Update, context):
    q = update.callback_query
    platform = q.data[2:]
    context.user_data["platform"] = platform
    
    btns = [
        [InlineKeyboardButton("💳 Buy Now", callback_data="buy"), InlineKeyboardButton(f"🎁 Free ({POINT_COST} Pts)", callback_data="free")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    await q.edit_message_text(f"🎬 Platform: **{platform}**\n\nChoose your option:", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def action(update: Update, context):
    q = update.callback_query
    user_id = str(q.from_user.id)
    
    if q.data == "back":
        await main_menu(update, context)
        return
    
    if q.data == "buy":
        await q.edit_message_text(
            f"💳 **PAYMENT METHODS**\n\n"
            f"🔸 **Binance ID:** `791001890`\n"
            f"🔸 **PayPal:** `raoufeboukhamla18@gmail.com`\n\n"
            f"📩 Contact Owner: {CONTACT_USERNAME}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]),
            parse_mode="Markdown"
        )
        return

    if q.data == "free":
        platform = context.user_data.get("platform")
        if users[user_id]["points"] < POINT_COST:
            link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await q.edit_message_text(f"❌ Not enough points!\nInvite 3 friends to get a free account.\n\nYour Link:\n`{link}`", parse_mode="Markdown")
            return

        acc = deliver_account(platform)
        if not acc:
            await q.edit_message_text(f"⚠️ **{platform}** is currently Out of Stock!")
            return

        users[user_id]["points"] -= POINT_COST
        save_users(users)

        await q.edit_message_text(f"✅ **Success!**\n\nPlatform: {platform}\nAccount: `{acc}`\n\nPoints Deducted: {POINT_COST}", parse_mode="Markdown")

        # LOGS (No account info shown for safety)
        log_msg = f"🔔 **LOG:** {q.from_user.first_name} pulled {platform}. (Remaining Points: {users[user_id]['points']})"
        try: await context.bot.send_message(LOG_CHANNEL, log_msg)
        except: pass

# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_platform, pattern="^p_"))
app.add_handler(CallbackQueryHandler(action, pattern="^(buy|free|back)$"))
app.run_polling()import json, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"

ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
CONTACT_USERNAME = "@q5mww"

REQUIRED_CHANNELS = [
    ("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free"),
    ("@freebroorsell", "https://t.me/freebroorsell")
]

PLATFORMS = [
    "Netflix","Prime Video","Disney+",
    "Hulu","HBO Max","Crunchyroll",
    "HIDIVE","Apple TV","Paramount+",
    "YouTube Premium","Spotify Premium","Deezer",
    "Hotstar","Steam","Xbox","PSN"
]

POINT_COST = 3


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
            "points": 0,
            "ref_by": None,
            "invited": []
        }

    # ================= REFERRAL FIX =================
    if context.args:
        ref_id = context.args[0]

        if (
            ref_id != user_id and
            ref_id in users and
            users[user_id]["ref_by"] is None
        ):
            users[user_id]["ref_by"] = ref_id
            users[ref_id]["points"] += 1
            users[ref_id]["invited"].append(user_id)

    save_users(users)

    # ================= MEMBERSHIP =================
    if not await is_member(context.bot, user.id):

        buttons = []

        for name, link in REQUIRED_CHANNELS:
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=link)])

        buttons.append([InlineKeyboardButton("✅ Verify", callback_data="check")])

        text = "🚨 To use the bot, please join required channels first."

        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    await main_menu(update, context)


# ================= MAIN MENU =================

async def main_menu(update, context):

    user = update.effective_user
    user_id = str(user.id)
    points = users[user_id]["points"]

    buttons = []

    # grid 3 per row
    row = []
    for p in PLATFORMS:
        row.append(InlineKeyboardButton(p, callback_data=f"p_{p}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    text = (
        f"✨ Welcome {user.first_name}\n\n"
        f"🎯 Your Points: {points}\n"
        f"💎 Cost per account: {POINT_COST} points\n\n"
        f"👇 Select Platform"
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ================= VERIFY =================

async def check(update: Update, context):
    q = update.callback_query
    await q.answer()

    if await is_member(context.bot, q.from_user.id):
        await main_menu(update, context)
    else:
        await q.answer("❌ You are not subscribed yet!", show_alert=True)


# ================= PLATFORM =================

async def choose_platform(update: Update, context):
    q = update.callback_query
    await q.answer()

    platform = q.data[2:]
    context.user_data["platform"] = platform

    buttons = [
        [InlineKeyboardButton("💳 Buy", callback_data="buy")],
        [InlineKeyboardButton("🎁 Free (3 Points)", callback_data="free")],
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

    platform = context.user_data.get("platform")

    if not platform:
        await q.edit_message_text("⚠ Session expired. Press /start again.")
        return

    if q.data == "buy":
        await q.edit_message_text(
            f"💳 Payment Methods\n\n"
            f"Binance ID: 791001890\n"
            f"PayPal: raoufeboukhamla18@gmail.com\n\n"
            f"📩 Contact: {CONTACT_USERNAME}"
        )
        return

    if q.data == "free":

        if users[user_id]["points"] < POINT_COST:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await q.edit_message_text(
                f"❌ Not enough points\n\n"
                f"Points: {users[user_id]['points']}/{POINT_COST}\n\n"
                f"Invite friends:\n{ref_link}"
            )
            return

        users[user_id]["points"] -= POINT_COST
        save_users(users)

        await q.edit_message_text(
            f"✅ Account delivered for {platform}\n\n"
            f"(Demo Mode)"
        )

        await context.bot.send_message(
            LOG_CHANNEL,
            f"New Delivery\nUser: {user_id}\nPlatform: {platform}"
        )


# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check, pattern="check"))
app.add_handler(CallbackQueryHandler(choose_platform, pattern="^p_"))
app.add_handler(CallbackQueryHandler(action, pattern="^(buy|free|back)$"))

app.run_polling()
