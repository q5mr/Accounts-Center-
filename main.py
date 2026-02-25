import json, os, random, logging, asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# --- إعدادات السجلات (Logs) ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الأساسية (التوكن والأيدي) ---
# تم وضع التوكن مباشرة هنا لتجنب خطأ No address associated with hostname
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI"
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"

# --- السياسة المالية للبوت ---
POINT_COST = 3.0
DAILY_REWARD = 0.2
INVITE_REWARD = 1.0

PLATFORMS = {
    "Netflix": "🔴", "Spotify": "🟢", "Steam": "⚙️", "Disney+": "🟦", 
    "HBO": "🟣", "Xbox": "🟩", "Prime": "🔵", "Hulu": "🟢",
    "PSN": "🔷", "Apple TV": "🍎", "Crunchyroll": "🟠"
}

REQUIRED_CHANNELS = [
    ("@dayli_cookies_for_free", "https://t.me/dayli_cookies_for_free"),
    ("@freebroorsell", "https://t.me/freebroorsell")
]

# ================= إدارة البيانات (Data Management) =================

def load_data():
    if not os.path.exists("data.json"): 
        return {"users": {}, "gift_links": {}, "redeem_codes": {}}
    try:
        with open("data.json", "r", encoding="utf-8") as f: 
            return json.load(f)
    except: 
        return {"users": {}, "gift_links": {}, "redeem_codes": {}}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_data()

# ================= الوظائف المساعدة =================

async def is_member(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch_username, _ in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch_username, user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

def deliver_acc(platform):
    file_path = f"{platform}.txt"
    if not os.path.exists(file_path): return None
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines: return None
    acc = random.choice(lines)
    lines.remove(acc)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return acc

# ================= الأوامر الأساسية =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    u_id = str(update.effective_user.id)
    args = context.args
    
    # إضافة المستخدم الجديد
    if u_id not in db["users"]:
        ref = args[0] if args and args[0] in db["users"] and args[0] != u_id else None
        db["users"][u_id] = {"points": 10.0 if int(u_id) == ADMIN_ID else 0.0, "last_daily": None}
        if ref:
            db["users"][ref]["points"] += INVITE_REWARD
            try: await context.bot.send_message(ref, f"👤 شخص انضم عبر رابطك! حصلت على {INVITE_REWARD} نقطة.")
            except: pass
        save_data(db)

    # معالجة روابط الهدايا (Gift Links)
    if args and args[0].startswith("gift_"):
        gift_id = args[0]
        if gift_id in db["gift_links"]:
            gift = db["gift_links"][gift_id]
            if u_id not in gift["claimed_by"] and len(gift["claimed_by"]) < gift["max_uses"]:
                db["users"][u_id]["points"] += gift["amount"]
                gift["claimed_by"].append(u_id)
                save_data(db)
                await update.message.reply_text(f"🎁 مبروك! حصلت على {gift['amount']} نقطة من رابط الهدية.")
            else:
                await update.message.reply_text("❌ هذا الرابط انتهى أو حصلت عليه مسبقاً.")
        return

    # التحقق من الاشتراك الإجباري
    if not await is_member(context.bot, update.effective_user.id):
        btns = [[InlineKeyboardButton(f"Join {ch}", url=link)] for ch, link in REQUIRED_CHANNELS]
        await update.message.reply_text("👋 أهلاً بك! يرجى الاشتراك في القنوات أدناه لتتمكن من استخدام البوت:", 
                                       reply_markup=InlineKeyboardMarkup(btns))
        return

    await show_main_menu(update, context)

async def show_main_menu(update, context):
    u_id = str(update.effective_user.id)
    pts = round(db["users"][u_id]["points"], 2)
    
    kb = []
    row = []
    for plat, emoji in PLATFORMS.items():
        row.append(InlineKeyboardButton(f"{emoji} {plat}", callback_data=f"buy_{plat}"))
        if len(row) == 2: kb.append(row); row = []
    if row: kb.append(row)
    
    kb.append([InlineKeyboardButton("📅 هدية يومية", callback_data="daily"), InlineKeyboardButton("🔑 كود تفعيل", callback_data="redeem")])
    kb.append([InlineKeyboardButton("🔗 رابط الإحالة", callback_data="ref")])

    text = f"✨ **Elite Digital Store** ✨\n\n💰 نقاطك: `{pts}`\n━━━━━━━━━━━━━━"
    
    if update.callback_query: 
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: 
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ================= معالجة الأزرار والقائمة =================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    u_id = str(query.from_user.id)
    data = query.data
    await query.answer()

    if data == "daily":
        last = db["users"][u_id].get("last_daily")
        now = datetime.now()
        if last and (now - datetime.fromisoformat(last)) < timedelta(hours=24):
            diff = timedelta(hours=24) - (now - datetime.fromisoformat(last))
            await query.answer(f"⏳ عد بعد {int(diff.total_seconds() // 3600)} ساعة", show_alert=True)
        else:
            db["users"][u_id]["points"] += DAILY_REWARD
            db["users"][u_id]["last_daily"] = now.isoformat()
            save_data(db)
            await query.answer(f"🎁 حصلت على {DAILY_REWARD} نقطة!", show_alert=True)
            await show_main_menu(update, context)

    elif data.startswith("buy_"):
        plat = data.split("_")[1]
        if db["users"][u_id]["points"] < POINT_COST:
            await query.answer(f"❌ تحتاج {POINT_COST} نقطة!", show_alert=True)
            return
        
        acc = deliver_acc(plat)
        if acc:
            db["users"][u_id]["points"] -= POINT_COST
            save_data(db)
            await query.edit_message_text(f"✅ تم تسليم حساب {plat}:\n\n`{acc}`", parse_mode="Markdown")
            await context.bot.send_message(LOG_CHANNEL, f"📦 مبيعات: {plat} للمستخدم {u_id}")
        else:
            await query.answer("⚠️ نفذ المخزون!", show_alert=True)

    elif data == "redeem":
        await query.edit_message_text("⌨️ أرسل كود التفعيل الآن:")
        context.user_data["waiting"] = "code"

    elif data == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start={u_id}"
        await query.edit_message_text(f"🔗 رابط الإحالة الخاص بك:\n`{link}`\n\nكل شخص ينضم تحصل على {INVITE_REWARD} نقطة.", 
                                    parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

    elif data == "home": await show_main_menu(update, context)

# ================= معالجة الرسائل النصية =================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    u_id = str(update.effective_user.id)
    text = update.message.text
    
    # تفعيل الكود
    if context.user_data.get("waiting") == "code":
        if text in db["redeem_codes"]:
            amt = db["redeem_codes"][text]
            db["users"][u_id]["points"] += amt
            del db["redeem_codes"][text]
            save_data(db)
            await update.message.reply_text(f"✅ مبروك! تم تفعيل الكود وحصلت على {amt} نقطة.")
            context.user_data["waiting"] = None
        else:
            await update.message.reply_text("❌ الكود خاطئ أو مستخدم.")
        return

    # أوامر الأدمن
    if int(u_id) == ADMIN_ID:
        if text.startswith("صنع هدية"): # صنع هدية 1 5
            parts = text.split(" ")
            if len(parts) == 4:
                amt, mx = parts[2], parts[3]
                g_id = f"gift_{random.randint(100, 9999)}"
                db["gift_links"][g_id] = {"amount": float(amt), "max_uses": int(mx), "claimed_by": []}
                save_data(db)
                await update.message.reply_text(f"✅ رابط الهدية جاهز:\nhttps://t.me/{BOT_USERNAME}?start={g_id}")
        
        elif text.startswith("صنع كود"): # صنع كود FREE10 10
            parts = text.split(" ")
            if len(parts) == 4:
                code, amt = parts[2], parts[3]
                db["redeem_codes"][code] = float(amt)
                save_data(db)
                await update.message.reply_text(f"✅ تم إنشاء الكود `{code}` بقيمة {amt} نقاط.")

# ================= التشغيل النهائي (Main) =================

if __name__ == '__main__':
    # تهيئة التطبيق مع أوقات مهلة طويلة لتفادي NetworkError
    app = ApplicationBuilder().token(TOKEN).connect_timeout(40).read_timeout(40).write_timeout(40).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("🤖 BOT IS LIVE AND RUNNING!")
    # استخدام drop_pending_updates لتجنب التراكم عند إعادة التشغيل
    app.run_polling(drop_pending_updates=True)
