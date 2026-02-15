import json, os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
CONTACT_USERNAME = "@q5mww"
POINT_COST = 3

# المنصات مع الإيموجي (يجب أن تكون أسماء الملفات بنفس هذه الأسماء .txt)
PLATFORMS = {
    "Netflix": "🔴", "Prime": "🔵", "Disney+": "🟦", "Hulu": "🟢",
    "HBO": "🟣", "Crunchyroll": "🟠", "Spotify": "🟢", "Steam": "⚙️",
    "Xbox": "🟩", "PSN": "🔷", "HIDIVE": "🐳", "Apple TV": "🍎"
}

REQUIRED_CHANNELS = [
    ("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free"),
    ("@freebroorsell", "https://t.me/freebroorsell")
]

# --- إدارة قاعدة البيانات ---
def load_users():
    if not os.path.exists("users.json"): return {}
    try:
        with open("users.json", "r") as f: return json.load(f)
    except: return {}

def save_users(data):
    with open("users.json", "w") as f: json.dump(data, f, indent=4)

users = load_users()

# --- نظام المخزون (السحب العشوائي) ---
def deliver_account(platform):
    file_name = f"{platform}.txt"
    if not os.path.exists(file_name): return None
    
    with open(file_name, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines: return None
    
    # اختيار عشوائي وحذف الحساب من القائمة
    account = random.choice(lines)
    lines.remove(account)
    
    # تحديث الملف بعد الحذف
    with open(file_name, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    
    return account

# --- التحقق من الاشتراك الإجباري ---
async def is_member(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch, _ in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

# --- الأوامر الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    # تسجيل مستخدم جديد ونظام الإحالة
    if user_id not in users:
        # التحقق من وجود كود إحالة في الرابط
        referrer_id = context.args[0] if context.args else None
        
        users[user_id] = {
            "points": 999999 if user.id == ADMIN_ID else 0,
            "ref_by": referrer_id,
            "invited": []
        }
        
        # إضافة نقطة للمدعو (إذا كان موجوداً وغير نفسه)
        if referrer_id and referrer_id in users and referrer_id != user_id:
            if user_id not in users[referrer_id]["invited"]:
                users[referrer_id]["points"] += 1
                users[referrer_id]["invited"].append(user_id)
                try:
                    await context.bot.send_message(referrer_id, f"🎉 عضو جديد انضم عبر رابطك! حصلت على 1 نقطة.")
                except: pass
        save_users(users)

    # فحص الاشتراك
    if not await is_member(context.bot, user.id):
        buttons = [[InlineKeyboardButton("📢 Join Channel", url=link)] for _, link in REQUIRED_CHANNELS]
        await update.message.reply_text(
            "⚠️ عذراً! يجب عليك الاشتراك في القنوات الرسمية لاستخدام البوت.\n\nبعد الاشتراك، أرسل /start مجدداً.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
        
    await main_menu(update, context)

async def main_menu(update, context):
    user = update.effective_user
    user_id = str(user.id)
    points = users.get(user_id, {}).get("points", 0)
    
    buttons = []
    row = []
    for name, emoji in PLATFORMS.items():
        row.append(InlineKeyboardButton(f"{emoji} {name}", callback_data=f"p_{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: buttons.append(row)

    text = (
        f"👋 أهلاً بك {user.first_name}\n"
        f"🎯 رصيد نقاطك: {points}\n"
        f"👤 الآيدي الخاص بك: `{user_id}`\n\n"
        f"🛒 اختر المنصة التي تريد الحصول عليها:"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def choose_platform(update: Update, context):
    q = update.callback_query
    await q.answer()
    platform = q.data[2:]
    context.user_data["platform"] = platform
    
    buttons = [
        [InlineKeyboardButton("💳 شراء مباشر", callback_data="buy"), 
         InlineKeyboardButton(f"🎁 مجاناً ({POINT_COST} نقاط)", callback_data="free")],
        [InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="back")]
    ]
    
    await q.edit_message_text(
        f"🎬 منصة: **{platform}**\n\nكيف ترغب في الحصول على الحساب؟",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def action(update: Update, context):
    q = update.callback_query
    user_id = str(q.from_user.id)
    
    if q.data == "back":
        await main_menu(update, context)
        return
    
    if q.data == "buy":
        await q.edit_message_text(
            f"💳 **للحصول على حساب مدفوع فوراً:**\n\nتواصل مع المالك: {CONTACT_USERNAME}\n\n"
            "طرق الدفع:\n- Binance ID: `791001890`\n- PayPal",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back")]]),
            parse_mode="Markdown"
        )
        return

    if q.data == "free":
        platform = context.user_data.get("platform")
        
        # التأكد من النقاط
        if users[user_id]["points"] < POINT_COST:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await q.edit_message_text(
                f"❌ نقاطك غير كافية! تحتاج إلى {POINT_COST} نقاط.\n\n"
                f"شارك رابطك مع أصدقائك للحصول على نقاط:\n`{ref_link}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back")]]),
                parse_mode="Markdown"
            )
            return

        # محاولة السحب العشوائي
        account = deliver_account(platform)
        
        if not account:
            await q.edit_message_text(
                f"⚠️ عذراً، مخزون **{platform}** فارغ حالياً.\nسيتم إشعار الإدارة لتوفيره قريباً.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back")]]),
                parse_mode="Markdown"
            )
            return

        # خصم النقاط وحفظ البيانات
        users[user_id]["points"] -= POINT_COST
        save_users(users)

        # إرسال الحساب للمستخدم
        await q.edit_message_text(
            f"✅ تم سحب حساب **{platform}** بنجاح!\n\n"
            f"🔑 الحساب:\n`{account}`\n\n"
            f"💰 الخصم: {POINT_COST} نقاط.\n"
            f"📊 رصيدك المتبقي: {users[user_id]['points']}",
            parse_mode="Markdown"
        )

        # سجل العمليات للقناة (بدون بيانات الحساب لضمان الخصوصية)
        log_msg = (
            f"🔔 **عملية سحب جديدة**\n"
            f"👤 المستخدم: {q.from_user.first_name}\n"
            f"🆔 الآيدي: `{user_id}`\n"
            f"🎮 المنصة: {platform}\n"
            f"📉 الخصم: {POINT_COST} نقاط\n"
            f"📊 رصيده الآن: {users[user_id]['points']}"
        )
        try:
            await context.bot.send_message(LOG_CHANNEL, log_msg, parse_mode="Markdown")
        except: pass

# --- تشغيل البوت ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_platform, pattern="^p_"))
app.add_handler(CallbackQueryHandler(action, pattern="^(buy|free|back)$"))

print("✅ Bot is running...")
app.run_polling()
