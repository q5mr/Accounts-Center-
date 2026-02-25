import json, os, random, logging, asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# --- إعدادات السجلات ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الأساسية ---
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI" # غيره إذا قمت بعمل Revoke
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"

# --- السياسة المالية للبوت ---
POINT_COST = 3.0
MYSTERY_BOX_COST = 2.0
INVITE_REWARD = 1.0
DAILY_REWARD = 0.2

PLATFORMS = {"Netflix": "🔴", "Spotify": "🟢", "Steam": "⚙️", "Disney+": "🟦", "HBO": "🟣", "Xbox": "🟩"}

# ================= إدارة البيانات =================

def load_data():
    if not os.path.exists("data.json"): 
        return {"users": {}, "gift_links": {}, "redeem_codes": {}}
    with open("data.json", "r") as f: return json.load(f)

def save_data(data):
    with open("data.json", "w") as f: json.dump(data, f, indent=4)

db = load_data()

# ================= الوظائف الذكية =================

def get_rank(points):
    if points < 10: return "🥉 برونزي"
    if points < 50: return "🥈 فضي"
    return "🥇 ذهبي"

def deliver_random_acc(platform):
    file_path = f"{platform}.txt"
    if not os.path.exists(file_path): return None
    with open(file_path, "r") as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines: return None
    acc = random.choice(lines)
    lines.remove(acc)
    with open(file_path, "w") as f:
        f.write("\n".join(lines))
    return acc

# ================= الأوامر =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = str(update.effective_user.id)
    args = context.args
    
    # 1. تسجيل مستخدم جديد
    if u_id not in db["users"]:
        ref = args[0] if args and args[0] in db["users"] and args[0] != u_id else None
        db["users"][u_id] = {
            "points": 0.0, "last_daily": None, "is_banned": False, "total_refs": 0
        }
        if ref:
            db["users"][ref]["points"] += INVITE_REWARD
            db["users"][ref]["total_refs"] += 1
            try: await context.bot.send_message(ref, f"👤 شخص انضم عبر رابطك! حصلت على {INVITE_REWARD} نقطة.")
            except: pass
        
        save_data(db)
        # إشعار للمدير
        await context.bot.send_message(ADMIN_ID, f"🆕 مستخدم جديد انضم: `{u_id}`", parse_mode="Markdown")

    # 2. فحص هل الرابط هو "رابط هدية" (Gift Link)
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

    await show_main_menu(update, context)

async def show_main_menu(update, context):
    u_id = str(update.effective_user.id)
    user = db["users"][u_id]
    
    kb = [
        [InlineKeyboardButton("🛒 شراء حساب", callback_data="buy_list"), InlineKeyboardButton("🎁 صندوق الحظ", callback_data="lucky")],
        [InlineKeyboardButton("📅 هدية يومية", callback_data="daily"), InlineKeyboardButton("🏆 المتصدرين", callback_data="top")],
        [InlineKeyboardButton("🔗 رابط الإحالة", callback_data="my_ref"), InlineKeyboardButton("🔑 كود تفعيل", callback_data="redeem")]
    ]
    
    text = (
        f"👋 أهلاً بك {update.effective_user.first_name}\n"
        f"💰 نقاطك: `{round(user['points'], 2)}`\n"
        f"🎖 رتبتك: {get_rank(user['points'])}\n"
        "━━━━━━━━━━━━━━"
    )
    
    if update.callback_query: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ================= التفاعلات =================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    u_id = str(query.from_user.id)
    data = query.data
    await query.answer()

    if data == "buy_list":
        btns = [[InlineKeyboardButton(f"{e} {p}", callback_data=f"get_{p}")] for p, e in PLATFORMS.items()]
        btns.append([InlineKeyboardButton("🔙 عودة", callback_data="home")])
        await query.edit_message_text("اختر المنصة:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("get_"):
        plat = data.split("_")[1]
        if db["users"][u_id]["points"] < POINT_COST:
            await query.answer("❌ نقاطك غير كافية!", show_alert=True)
            return
        
        acc = deliver_random_acc(plat)
        if acc:
            db["users"][u_id]["points"] -= POINT_COST
            save_data(db)
            await query.edit_message_text(f"✅ تم تسليم حساب {plat}:\n`{acc}`", parse_mode="Markdown")
            await context.bot.send_message(LOG_CHANNEL, f"✅ مبيعات: {plat} للمستخدم {u_id}")
        else:
            await query.answer("⚠️ نفذ المخزون!", show_alert=True)

    elif data == "daily":
        last = db["users"][u_id].get("last_daily")
        now = datetime.now()
        if last and (now - datetime.fromisoformat(last)) < timedelta(hours=24):
            diff = timedelta(hours=24) - (now - datetime.fromisoformat(last))
            await query.answer(f"⏳ عد بعد {int(diff.total_seconds() // 3600)} ساعة", show_alert=True)
        else:
            db["users"][u_id]["points"] = round(db["users"][u_id]["points"] + DAILY_REWARD, 2)
            db["users"][u_id]["last_daily"] = now.isoformat()
            save_data(db)
            await query.answer(f"🎁 مبروك! حصلت على {DAILY_REWARD} نقطة", show_alert=True)
            await show_main_menu(update, context)

    elif data == "redeem":
        await query.edit_message_text("⌨️ أرسل كود التفعيل الآن:")
        context.user_data["waiting_for"] = "redeem_code"

    elif data == "home": await show_main_menu(update, context)

# ================= أوامر المدير (Gift & Redeem) =================

async def admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = update.message.text
    u_id = str(update.effective_user.id)

    # 1. صنع رابط هدية: (صنع هدية 2 10) -> يعطي 2 نقاط لـ 10 أشخاص
    if text.startswith("صنع هدية"):
        _, _, amount, max_u = text.split(" ")
        g_id = f"gift_{random.randint(1000, 9999)}"
        db["gift_links"][g_id] = {"amount": float(amount), "max_uses": int(max_u), "claimed_by": []}
        save_data(db)
        link = f"https://t.me/{BOT_USERNAME}?start={g_id}"
        await update.message.reply_text(f"✅ تم إنشاء رابط الهدية:\n{link}")

    # 2. صنع كود تفعيل: (صنع كود FREE50 5) -> كود يعطي 5 نقاط
    elif text.startswith("صنع كود"):
        _, _, code, amount = text.split(" ")
        db["redeem_codes"][code] = float(amount)
        save_data(db)
        await update.message.reply_text(f"✅ تم إنشاء الكود `{code}` بقيمة {amount} نقاط.", parse_mode="Markdown")

# ================= استقبال النصوص =================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = str(update.effective_user.id)
    text = update.message.text
    
    if context.user_data.get("waiting_for") == "redeem_code":
        if text in db["redeem_codes"]:
            pts = db["redeem_codes"][text]
            db["users"][u_id]["points"] += pts
            del db["redeem_codes"][text] # الكود يستخدم لمرة واحدة
            save_data(db)
            await update.message.reply_text(f"✅ مبروك! تم تفعيل الكود وحصلت على {pts} نقطة.")
            context.user_data["waiting_for"] = None
        else:
            await update.message.reply_text("❌ الكود خاطئ أو تم استخدامه سابقاً.")
        return

    if u_id == str(ADMIN_ID): await admin_msg(update, context)

# ================= التشغيل =================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("🤖 BOT UPDATED & READY!")
    app.run_polling()
