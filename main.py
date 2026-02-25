import json, os, random, logging, asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# --- الإعدادات الأساسية ---
TOKEN = "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI" # غيره فوراً!
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"
BOT_USERNAME = "F_F_i3_bot"
POINT_COST = 3
MYSTERY_BOX_COST = 2 # سعر أرخص لصندوق الحظ

# --- القواميس والبيانات ---
STRINGS = {
    "ar": {
        "welcome": "👋 أهلاً بك في المتجر الأذكى!\n\n💰 نقاطك: `{pts}`\n🎖 رتبتك: `{rank}`",
        "select_lang": "الرجاء اختيار اللغة / Please select a language:",
        "main_menu": "القائمة الرئيسية 🛒",
        "buy": "🛒 شراء حساب",
        "lucky": "🎁 صندوق الحظ",
        "daily": "📅 هدية يومية",
        "top": "🏆 المتصدرين",
        "lang": "🌐 اللغة",
        "no_pts": "❌ نقاطك غير كافية! شارك رابطك: \n",
        "out_stock": "⚠️ نفذ المخزون! تم إرسال تنبيه للإدارة.",
        "daily_done": "🎉 حصلت على 1 نقطة هدية! عد غداً.",
        "daily_wait": "⏳ لقد حصلت على هديتك بالفعل، عد بعد {h} ساعة.",
    },
    "en": {
        "welcome": "👋 Welcome to the Smartest Store!\n\n💰 Points: `{pts}`\n🎖 Rank: `{rank}`",
        "select_lang": "Please select a language:",
        "main_menu": "Main Menu 🛒",
        "buy": "🛒 Buy Account",
        "lucky": "🎁 Mystery Box",
        "daily": "📅 Daily Gift",
        "top": "🏆 Leaderboard",
        "lang": "🌐 Language",
        "no_pts": "❌ Not enough points! Share your link: \n",
        "out_stock": "⚠️ Out of stock! Admin has been notified.",
        "daily_done": "🎉 You got 1 free point! Come back tomorrow.",
        "daily_wait": "⏳ Already claimed, come back in {h} hours.",
    }
}

PLATFORMS = {"Netflix": "🔴", "Spotify": "🟢", "Steam": "⚙️", "Disney+": "🟦", "Hulu": "🟢"}

# ================= DATABASE =================

def load_data():
    if not os.path.exists("users.json"): return {}
    with open("users.json", "r") as f: return json.load(f)

def save_data(data):
    with open("users.json", "w") as f: json.dump(data, f, indent=4)

users = load_data()

# ================= LOGIC FUNCTIONS =================

def get_rank(points):
    if points < 10: return "🥉 برونزي"
    if points < 50: return "🥈 فضي"
    return "🥇 ذهبي"

def deliver_random_account(platform):
    file_path = f"{platform}.txt"
    if not os.path.exists(file_path): return None
    
    with open(file_path, "r") as f:
        accounts = [line.strip() for line in f if line.strip()]
    
    if not accounts: return None
    
    selected = random.choice(accounts)
    accounts.remove(selected)
    
    with open(file_path, "w") as f:
        f.write("\n".join(accounts))
    
    return selected

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = str(update.effective_user.id)
    if u_id not in users:
        ref = context.args[0] if context.args and context.args[0] in users else None
        users[u_id] = {
            "points": 0, "lang": "ar", "last_daily": None, 
            "is_banned": False, "total_bought": 0
        }
        if ref:
            users[ref]["points"] += 1
            try: await context.bot.send_message(ref, "🤝 صديقك انضم! حصلت على نقطة.")
            except: pass
        save_data(users)
    
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="setlang_ar"),
         InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en")]
    ]
    await update.message.reply_text("🌐 Select Language / اختر اللغة", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_main_menu(update, context):
    query = update.callback_query
    u_id = str(update.effective_user.id)
    lang = users[u_id]["lang"]
    pts = users[u_id]["points"]
    rank = get_rank(pts)
    
    txt = STRINGS[lang]
    keyboard = [
        [InlineKeyboardButton(txt["buy"], callback_data="list_platforms"), InlineKeyboardButton(txt["lucky"], callback_data="mystery_box")],
        [InlineKeyboardButton(txt["daily"], callback_data="get_daily"), InlineKeyboardButton(txt["top"], callback_data="show_top")],
        [InlineKeyboardButton(txt["lang"], callback_data="change_lang")]
    ]
    
    msg_text = txt["welcome"].format(pts=pts, rank=rank)
    if query: await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else: await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ================= HANDLERS =================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    u_id = str(query.from_user.id)
    data = query.data
    lang = users[u_id]["lang"]
    txt = STRINGS[lang]
    
    await query.answer()

    if data.startswith("setlang_"):
        users[u_id]["lang"] = data.split("_")[1]
        save_data(users)
        await show_main_menu(update, context)

    elif data == "list_platforms":
        keyboard = []
        for p, e in PLATFORMS.items():
            keyboard.append([InlineKeyboardButton(f"{e} {p}", callback_data=f"buy_{p}")])
        keyboard.append([InlineKeyboardButton("🔙", callback_data="back_home")])
        await query.edit_message_text("Choose Platform:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_"):
        platform = data.split("_")[1]
        if users[u_id]["points"] < POINT_COST:
            link = f"https://t.me/{BOT_USERNAME}?start={u_id}"
            await query.edit_message_text(f"{txt['no_pts']}`{link}`", parse_mode="Markdown")
            return
        
        acc = deliver_random_account(platform)
        if acc:
            users[u_id]["points"] -= POINT_COST
            save_data(users)
            await query.edit_message_text(f"✅ Your Account:\n`{acc}`", parse_mode="Markdown")
        else:
            await query.edit_message_text(txt["out_stock"])
            await context.bot.send_message(LOG_CHANNEL, f"🚨 Out of stock: {platform}")

    elif data == "get_daily":
        last = users[u_id].get("last_daily")
        now = datetime.now()
        if last and (now - datetime.fromisoformat(last)) < timedelta(hours=24):
            diff = timedelta(hours=24) - (now - datetime.fromisoformat(last))
            await query.answer(txt["daily_wait"].format(h=int(diff.seconds // 3600)), show_alert=True)
        else:
            users[u_id]["points"] += 1
            users[u_id]["last_daily"] = now.isoformat()
            save_data(users)
            await query.answer(txt["daily_done"], show_alert=True)
            await show_main_menu(update, context)

    elif data == "mystery_box":
        if users[u_id]["points"] < MYSTERY_BOX_COST:
            await query.answer("You need points!", show_alert=True)
            return
        
        # اختيار منصة عشوائية
        p_list = list(PLATFORMS.keys())
        plat = random.choice(p_list)
        acc = deliver_random_account(plat)
        
        if acc:
            users[u_id]["points"] -= MYSTERY_BOX_COST
            save_data(users)
            await query.edit_message_text(f"🎁 **Mystery Box Result ({plat}):**\n\n`{acc}`", parse_mode="Markdown")
        else:
            await query.answer("Bad luck! Empty box.", show_alert=True)

    elif data == "back_home":
        await show_main_menu(update, context)

# ================= RUN =================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🔥 Crazy Bot Started!")
    app.run_polling()
