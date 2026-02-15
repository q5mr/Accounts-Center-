import json, os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"
ADMIN_ID = 6808384195
VIP_ID = "6253574206" # الآيدي الذي سيحصل على نقاط لانهائية
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
CONTACT_USERNAME = "@q5mww"
POINT_COST = 3

# Platforms must match your .txt filenames exactly
PLATFORMS = {
    "Netflix": "🔴", "Prime": "🔵", "Disney+": "🟦", "Hulu": "🟢",
    "HBO": "🟣", "Crunchyroll": "🟠", "Spotify": "🟢", "Steam": "⚙️",
    "Xbox": "🟩", "PSN": "🔷", "HIDIVE": "🐳", "Apple TV": "🍎"
}

REQUIRED_CHANNELS = [
    ("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free"),
    ("@freebroorsell", "https://t.me/freebroorsell")
]

# --- TRANSLATIONS (نظام اللغات) ---
TRANSLATIONS = {
    "en": {
        "welcome": "✨ **DIGITAL STORE**\n\n👤 User: `{}`\n🎯 Points: **{}**\n\nSelect Platform:",
        "choose_lang": "🌐 Please select your language:",
        "join_channel": "🚨 You must join our channels first:",
        "join_btn": "📢 Join Channel",
        "buy_btn": "💳 Buy Now",
        "free_btn": "🎁 Free ({} Pts)",
        "back_btn": "🔙 Back",
        "settings_btn": "⚙️ Settings",
        "buy_text": "💳 **PAYMENT METHODS**\n\n🔸 **Binance ID:** `791001890`\n🔸 **PayPal:** `raoufeboukhamla18@gmail.com`\n\n📩 Contact: {}",
        "no_points": "❌ Not enough points!\nInvite 3 friends to get a free account.\n\nYour Link:\n`{}`",
        "out_stock": "⚠️ **{}** is currently Out of Stock!",
        "success": "✅ **Success!**\n\nPlatform: {}\nAccount: `{}`\n\nPoints Deducted: {}",
        "platform_title": "🎬 Platform: **{}**\n\nChoose your option:",
        "settings_menu": "⚙️ **Settings**\n\nChoose an option:",
        "change_lang_btn": "🌐 Change Language"
    },
    "ar": {
        "welcome": "✨ **المتجر الرقمي**\n\n👤 المستخدم: `{}`\n🎯 نقاطك: **{}**\n\nاختر المنصة:",
        "choose_lang": "🌐 من فضلك اختر لغة البوت:",
        "join_channel": "🚨 يجب عليك الاشتراك في قنواتنا أولاً:",
        "join_btn": "📢 اشتراك في القناة",
        "buy_btn": "💳 شراء مباشر",
        "free_btn": "🎁 مجاناً ({} نقاط)",
        "back_btn": "🔙 رجوع",
        "settings_btn": "⚙️ الإعدادات",
        "buy_text": "💳 **طرق الدفع**\n\n🔸 **Binance ID:** `791001890`\n🔸 **PayPal:** `raoufeboukhamla18@gmail.com`\n\n📩 للتواصل: {}",
        "no_points": "❌ نقاطك غير كافية!\nادعُ 3 أصدقاء للحصول على حساب مجاني.\n\nرابطك:\n`{}`",
        "out_stock": "⚠️ **{}** نفذ من المخزون حالياً!",
        "success": "✅ **تم السحب بنجاح!**\n\nالمنصة: {}\nالحساب: `{}`\n\nتم خصم: {} نقاط",
        "platform_title": "🎬 المنصة: **{}**\n\nاختر الطريقة:",
        "settings_menu": "⚙️ **الإعدادات**\n\nاختر خياراً:",
        "change_lang_btn": "🌐 تغيير اللغة"
    }
}

# --- DATABASE SYSTEM ---
def load_users():
    if not os.path.exists("users.json"): return {}
    try:
        with open("users.json", "r") as f: return json.load(f)
    except: return {}

def save_users(data):
    with open("users.json", "w") as f: json.dump(data, f, indent=4)

users = load_users()

# --- HELPER: Get Text based on User Lang ---
def get_text(user_id, key):
    lang = users.get(user_id, {}).get("lang", "en") # Default to English
    return TRANSLATIONS[lang].get(key, key)

# --- RANDOM STOCK SYSTEM ---
def deliver_account(platform):
    file_name = f"{platform}.txt"
    if not os.path.exists(file_name): return None
    
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
    
    # 1. تسجيل المستخدم الجديد
    if user_id not in users:
        ref_id = context.args[0] if context.args else None
        users[user_id] = {
            "points": 0, 
            "ref_by": ref_id, 
            "invited": [],
            "lang": None # لم يختر اللغة بعد
        }
        # نظام الإحالة
        if ref_id and ref_id in users and ref_id != user_id:
            users[ref_id]["points"] += 1
            users[ref_id]["invited"].append(user_id)
            try: await context.bot.send_message(ref_id, "🎁 +1 Point! New user joined.")
            except: pass
    
    # 2. منح نقاط للـ VIP (التعديل المطلوب)
    if user_id == VIP_ID:
        users[user_id]["points"] = 99999
        
    save_users(users)

    # 3. التحقق من الاشتراك
    if not await is_member(context.bot, user.id):
        lang = users[user_id].get("lang", "en") or "en"
        btns = [[InlineKeyboardButton(TRANSLATIONS[lang]["join_btn"], url=link)] for _, link in REQUIRED_CHANNELS]
        await update.message.reply_text(TRANSLATIONS[lang]["join_channel"], reply_markup=InlineKeyboardMarkup(btns))
        return

    # 4. التحقق من اللغة (إذا لم يتم اختيارها)
    if users[user_id].get("lang") is None:
        keyboard = [
            [InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en"),
             InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang_ar")]
        ]
        await update.message.reply_text("🌐 Please select your language / اختر لغتك:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await main_menu(update, context)

# --- LANGUAGE HANDLER ---
async def set_language(update: Update, context):
    q = update.callback_query
    user_id = str(q.from_user.id)
    lang_code = q.data.split("_")[-1] # ar or en
    
    if user_id not in users: users[user_id] = {"points": 0} # Safety
    
    users[user_id]["lang"] = lang_code
    save_users(users)
    
    await q.answer("Language saved / تم حفظ اللغة")
    await main_menu(update, context)

# --- SETTINGS MENU ---
async def settings_menu(update: Update, context):
    user_id = str(update.effective_user.id)
    text = get_text(user_id, "settings_menu")
    btn_text = get_text(user_id, "change_lang_btn")
    back_text = get_text(user_id, "back_btn")
    
    buttons = [
        [InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en"),
         InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang_ar")],
        [InlineKeyboardButton(back_text, callback_data="back")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

# --- MAIN MENU ---
async def main_menu(update, context):
    user_id = str(update.effective_user.id)
    pts = users.get(user_id, {}).get("points", 0)
    
    # جلب النصوص حسب اللغة
    welcome_text = get_text(user_id, "welcome").format(update.effective_user.first_name, pts)
    settings_text = get_text(user_id, "settings_btn")

    btns = []
    row = []
    for name, emoji in PLATFORMS.items():
        row.append(InlineKeyboardButton(f"{emoji} {name}", callback_data=f"p_{name}"))
        if len(row) == 3:
            btns.append(row); row = []
    if row: btns.append(row)
    
    # إضافة زر الإعدادات
    btns.append([InlineKeyboardButton(settings_text, callback_data="settings")])

    if update.message: 
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    else: 
        await update.callback_query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def choose_platform(update: Update, context):
    q = update.callback_query
    user_id = str(q.from_user.id)
    platform = q.data[2:]
    context.user_data["platform"] = platform
    
    # نصوص الأزرار
    buy_txt = get_text(user_id, "buy_btn")
    free_txt = get_text(user_id, "free_btn").format(POINT_COST)
    back_txt = get_text(user_id, "back_btn")
    title_txt = get_text(user_id, "platform_title").format(platform)

    btns = [
        [InlineKeyboardButton(buy_txt, callback_data="buy"), InlineKeyboardButton(free_txt, callback_data="free")],
        [InlineKeyboardButton(back_txt, callback_data="back")]
    ]
    await q.edit_message_text(title_txt, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def action(update: Update, context):
    q = update.callback_query
    user_id = str(q.from_user.id)
    
    if q.data == "back":
        await main_menu(update, context)
        return
    
    if q.data == "settings":
        await settings_menu(update, context)
        return
    
    if q.data == "buy":
        # التعديل المطلوب: زر رجوع في قائمة الدفع
        text = get_text(user_id, "buy_text").format(CONTACT_USERNAME)
        back_txt = get_text(user_id, "back_btn")
        
        await q.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_txt, callback_data="back")]]),
            parse_mode="Markdown"
        )
        return

    if q.data == "free":
        platform = context.user_data.get("platform")
        if users[user_id]["points"] < POINT_COST:
            link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            text = get_text(user_id, "no_points").format(link)
            back_txt = get_text(user_id, "back_btn")
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_txt, callback_data="back")]]), parse_mode="Markdown")
            return

        acc = deliver_account(platform)
        if not acc:
            text = get_text(user_id, "out_stock").format(platform)
            await q.edit_message_text(text)
            return

        users[user_id]["points"] -= POINT_COST
        save_users(users)

        text = get_text(user_id, "success").format(platform, acc, POINT_COST)
        await q.edit_message_text(text, parse_mode="Markdown")

        # LOGS
        log_msg = f"🔔 **LOG:** {q.from_user.first_name} pulled {platform}. (Remaining Points: {users[user_id]['points']})"
        try: await context.bot.send_message(LOG_CHANNEL, log_msg)
        except: pass

# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(set_language, pattern="^set_lang_"))
app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
app.add_handler(CallbackQueryHandler(choose_platform, pattern="^p_"))
app.add_handler(CallbackQueryHandler(action, pattern="^(buy|free|back)$"))

print("✅ Bot is running with Multi-Language Support...")
app.run_polling()
