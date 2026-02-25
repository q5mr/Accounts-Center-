import json, os, random, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# --- الإعدادات (يفضل وضعها في Environment Variables) ---
TOKEN = os.getenv("BOT_TOKEN", "8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI")
ADMIN_ID = 6808384195
LOG_CHANNEL = "@F_F_e8"

PLATFORMS = ["Netflix", "Spotify", "Steam", "Disney+", "HBO", "Xbox", "PSN"]

# ================= DATABASE =================
def load_data():
    if not os.path.exists("users.json"): return {}
    with open("users.json", "r") as f: return json.load(f)

def save_data(data):
    with open("users.json", "w") as f: json.dump(data, f, indent=4)

users = load_data()

# ================= CORE FUNCTIONS =================
def deliver_acc(platform):
    file_path = f"{platform}.txt"
    if not os.path.exists(file_path): return None
    with open(file_path, "r") as f:
        lines = f.readlines()
    if not lines: return None
    
    account = random.choice(lines).strip()
    lines.remove(account + '\n') if (account + '\n') in lines else lines.remove(account)
    
    with open(file_path, "w") as f:
        f.writelines(lines)
    return account

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = str(update.effective_user.id)
    if u_id not in users:
        users[u_id] = {"points": 10 if int(u_id) == ADMIN_ID else 0}
        save_data(users)
    
    kb = [[InlineKeyboardButton(f"🛒 Buy {p}", callback_data=f"buy_{p}")] for p in PLATFORMS]
    kb.append([InlineKeyboardButton("🏆 Leaderboard", callback_data="top"), InlineKeyboardButton("💰 Points", callback_data="pts")])
    
    await update.message.reply_text(
        f"🔥 **Welcome to the Elite Store**\nYour Points: `{users[u_id]['points']}`",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
    )

# ================= ADMIN ACTIONS (إضافة حسابات بالرسائل) =================
async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = update.message.text
    
    # مثال للأمر: أضف نيتفلكس user:pass
    if text.startswith("أضف "):
        parts = text.split(" ")
        if len(parts) >= 3:
            platform = parts[1]
            account = parts[2]
            with open(f"{platform}.txt", "a") as f:
                f.write(account + "\n")
            await update.message.reply_text(f"✅ تم إضافة الحساب إلى {platform}")

# ================= CALLBACKS =================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    u_id = str(q.from_user.id)
    await q.answer()

    if q.data.startswith("buy_"):
        p = q.data.split("_")[1]
        if users[u_id]["points"] < 3:
            await q.edit_message_text("❌ رصيدك غير كافٍ!")
            return
        
        acc = deliver_acc(p)
        if acc:
            users[u_id]["points"] -= 3
            save_data(users)
            await q.edit_message_text(f"✅ تم التسليم:\n`{acc}`", parse_mode="Markdown")
            await context.bot.send_message(LOG_CHANNEL, f"📦 تم شراء {p} من قبل {u_id}")
        else:
            await q.edit_message_text(f"⚠️ مخزون {p} فارغ!")

# ================= RUN =================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handler))
    app.run_polling()
