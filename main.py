import json
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الأساسية ---
# ملاحظة: غير التوكن فوراً لأنه أصبح مكشوفاً!
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
CONTACT_USERNAME = "@q5mww"
POINT_COST = 3

PLATFORMS = {
    "Netflix": "🔴", "Spotify": "🟢", "Steam": "⚙️", "Disney+": "🟦",
    "HBO": "🟣", "Xbox": "🟩", "PSN": "🔷", "Crunchyroll": "🟠"
}

REQUIRED_CHANNELS = [("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free")]

# ================= إدارة البيانات =================

def load_data():
    if not os.path.exists("users.json"): return {}
    with open("users.json", "r") as f: return json.load(f)

def save_data(data):
    with open("users.json", "w") as f: json.dump(data, f, indent=4)

users = load_data()

# ================= المحرك الأساسي =================

async def is_subscribed(bot, user_id):
    for ch, _ in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

# ================= أوامر المشرف (Admin) =================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    keyboard = [
        [InlineKeyboardButton("📢 إذاعة (Broadcast)", callback_data="adm_broadcast")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="adm_stats"), InlineKeyboardButton("🚫 حظر/إلغاء", callback_data="adm_ban")],
        [InlineKeyboardButton("💰 تعديل نقاط", callback_data="adm_points")]
    ]
    await update.message.reply_text("🛠 **لوحة تحكم المدير**", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= الأوامر العامة =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_id = str(user.id)
    
    # التحقق من الحظر
    if users.get(u_id, {}).get("is_banned", False):
        await update.message.reply_text("🚫 نأسف، لقد تم حظرك من استخدام البوت.")
        return

    # تسجيل المستخدم
    if u_id not in users:
        referrer = context.args[0] if context.args and context.args[0] in users else None
        users[u_id] = {"points": 0, "ref_by": referrer, "is_banned": False, "total_refs": 0}
        if referrer:
            users[referrer]["points"] += 1
            users[referrer]["total_refs"] += 1
            try: await context.bot.send_message(referrer, "🎉 حصلت على نقطة لدعوة صديق!")
            except: pass
        save_data(users)

    if not await is_subscribed(context.bot, user.id):
        btns = [[InlineKeyboardButton(f"✅ Join {ch}", url=l)] for ch, l in REQUIRED_CHANNELS]
        btns.append([InlineKeyboardButton("🔄 تحقق", callback_data="check_sub")])
        await update.message.reply_text("⚠️ اشترك بالقنوات أولاً!", reply_markup=InlineKeyboardMarkup(btns))
        return

    await main_menu(update, context)

async def main_menu(update, context):
    u_id = str(update.effective_user.id)
    pts = users[u_id]["points"]
    
    keyboard = []
    temp = []
    for p in PLATFORMS:
        temp.append(InlineKeyboardButton(f"{PLATFORMS[p]} {p}", callback_data=f"buy_{p}"))
        if len(temp) == 2: keyboard.append(temp); temp = []
    if temp: keyboard.append(temp)
    
    keyboard.append([InlineKeyboardButton("🏆 المتصدرين", callback_data="top_players"), InlineKeyboardButton("🔗 رابطي", callback_data="my_link")])
    
    text = f"✨ **متجر الحسابات**\n\n👤 العميل: {update.effective_user.first_name}\n💰 نقاطك: `{pts}`\n━━━━━━━━━━━━━━"
    
    if update.callback_query: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ================= نظام الـ TOP =================

async def show_top(update: Update, context):
    # ترتيب المستخدمين حسب النقاط (أعلى 10)
    top_list = sorted(users.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
    
    text = "🏆 **قائمة متصدري النقاط:**\n\n"
    for i, (uid, data) in enumerate(top_list, 1):
        text += f"{i} - `{uid}` ⇦ `{data['points']}` نقطة\n"
    
    await update.callback_query.edit_message_text(text, parse_mode="Markdown", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back_home")]]))

# ================= المعالجات (Callbacks) =================

async def handle_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    u_id = str(query.from_user.id)
    data = query.data
    
    if users.get(u_id, {}).get("is_banned", False): return

    if data == "back_home": await main_menu(update, context)
    
    elif data == "top_players": await show_top(update, context)
    
    elif data == "my_link":
        link = f"https://t.me/{BOT_USERNAME}?start={u_id}"
        await query.edit_message_text(f"🔗 رابط الإحالة الخاص بك:\n`{link}`\n\nكل شخص يدخل تحصل على 1 نقطة.", 
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back_home")]]))

    elif data.startswith("buy_"):
        plat = data.split("_")[1]
        # هنا تضع منطق التسليم الذي شرحناه سابقاً...
        await query.answer(f"محاولة شراء {plat}...", show_alert=True)

    # --- معالجة أوامر الإدارة ---
    elif data == "adm_stats":
        total = len(users)
        banned = sum(1 for u in users.values() if u.get("is_banned"))
        await query.edit_message_text(f"📊 إحصائيات البوت:\n\n👥 الأعضاء: {total}\n🚫 المحظورون: {banned}")

    elif data == "adm_broadcast":
        await query.edit_message_text("ارسل الآن الرسالة التي تريد إذاعتها لكل المستخدمين:")
        context.user_data["action"] = "broadcast"

# ================= نظام الاستقبال (للإذاعة والتحكم) =================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    action = context.user_data.get("action")
    
    if action == "broadcast":
        msg = update.message
        count = 0
        for uid in users:
            try:
                await msg.copy(chat_id=int(uid))
                count += 1
            except: pass
        await update.message.reply_text(f"✅ تمت الإذاعة لـ {count} مستخدم.")
        context.user_data["action"] = None

    # أمر سريع للحظر: اكتب (حظر 123456)
    if update.message.text.startswith("حظر "):
        target = update.message.text.split(" ")[1]
        if target in users:
            users[target]["is_banned"] = True
            save_data(users)
            await update.message.reply_text(f"🚫 تم حظر {target}")

    # أمر سريع للنقاط: اكتب (نقط 123456 50)
    if update.message.text.startswith("نقط "):
        _, target, amount = update.message.text.split(" ")
        if target in users:
            users[target]["points"] += int(amount)
            save_data(users)
            await update.message.reply_text(f"💰 تمت إضافة {amount} نقطة لـ {target}")

# ================= التشغيل =================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_actions))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🚀 BOT IS LIVE AND CRAZY!")
    app.run_polling()
