import os
import zipfile
import random
import psycopg2
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("8520184434:AAGnrmyjAkLpkvSZERLwqM9_g5QpvNe3uKI")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = "6808384195"
POINT_COST = 3

ACCOUNT_PLATFORMS = [
    "Netflix","Prime","Disney+","Hulu","HBO","Crunchyroll",
    "Spotify","Steam","Xbox","PSN","HIDIVE","Apple TV"
]

COOKIE_PLATFORMS = [
    "Netflix","Prime","Crunchyroll","ChatGPT","OSN"
]

REQUIRED_CHANNELS = [
    "@dayli_cookies_for_free",
    "@freebroorsell"
]

# ================= DATABASE =================
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0,
    language TEXT DEFAULT 'en',
    join_date TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions(
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    item_type TEXT,
    platform TEXT,
    date TIMESTAMP
)
""")

conn.commit()

# ================= DATABASE FUNCTIONS =================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=%s",(user_id,))
    return cursor.fetchone()

def create_user(user_id):
    if not get_user(user_id):
        cursor.execute(
            "INSERT INTO users VALUES(%s,0,'en',%s)",
            (user_id,datetime.utcnow())
        )
        conn.commit()

def get_points(user_id):
    cursor.execute("SELECT points FROM users WHERE user_id=%s",(user_id,))
    return cursor.fetchone()[0]

def update_points(user_id, amount):
    cursor.execute(
        "UPDATE users SET points=points+%s WHERE user_id=%s",
        (amount,user_id)
    )
    conn.commit()

def log_transaction(user_id,item_type,platform):
    cursor.execute(
        "INSERT INTO transactions(user_id,item_type,platform,date) VALUES(%s,%s,%s,%s)",
        (user_id,item_type,platform,datetime.utcnow())
    )
    conn.commit()

# ================= MEMBERSHIP CHECK =================
async def is_member(bot,user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            m = await bot.get_chat_member(ch,user_id)
            if m.status in ["left","kicked"]:
                return False
        except:
            return False
    return True

# ================= STOCK SYSTEM =================
def deliver_account(platform):
    path = f"{platform}.txt"

    if not os.path.exists(path):
        return None

    with open(path,"r",encoding="utf-8") as f:
        lines=[l.strip() for l in f if l.strip()]

    if not lines:
        return None

    item=random.choice(lines)
    lines.remove(item)

    with open(path,"w",encoding="utf-8") as f:
        for l in lines:
            f.write(l+"\n")

    return item

def deliver_cookie(platform):
    zip_path=f"{platform.lower()}.zip"

    if not os.path.exists(zip_path):
        return None

    with zipfile.ZipFile(zip_path,'r') as z:
        files=z.namelist()
        if not files:
            return None

        chosen=random.choice(files)
        data=z.read(chosen)

    # إعادة إنشاء zip بدون الملف المسحوب
    remaining=[]
    with zipfile.ZipFile(zip_path,'r') as z:
        for f in z.namelist():
            if f!=chosen:
                remaining.append((f,z.read(f)))

    with zipfile.ZipFile(zip_path,'w') as z:
        for name,data_file in remaining:
            z.writestr(name,data_file)

    return data.decode()

# ================= START =================
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    user_id=str(update.effective_user.id)
    create_user(user_id)

    if not await is_member(context.bot,update.effective_user.id):
        buttons=[
            [InlineKeyboardButton("📢 Join Channel 1",url="https://t.me/dayli_cookies_for_free")],
            [InlineKeyboardButton("📢 Join Channel 2",url="https://t.me/freebroorsell")],
            [InlineKeyboardButton("✅ Verify",callback_data="verify")]
        ]
        await update.message.reply_text(
            "Join channels then press Verify.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    pts=get_points(user_id)

    buttons=[
        [InlineKeyboardButton("🎁 Free (3 Points)",callback_data="free")],
        [InlineKeyboardButton("💳 Buy",callback_data="buy")]
    ]

    await update.message.reply_text(
        f"✨ DIGITAL STORE\n\nPoints: {pts}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= CALLBACK HANDLER =================
async def buttons(update:Update,context):
    q=update.callback_query
    await q.answer()
    user_id=str(q.from_user.id)

    if q.data=="verify":
        if await is_member(context.bot,q.from_user.id):
            await q.edit_message_text("✅ Verified. Send /start")
        else:
            await q.answer("❌ Not joined.",show_alert=True)

    elif q.data=="free":
        buttons=[
            [InlineKeyboardButton("👤 Accounts",callback_data="accounts")],
            [InlineKeyboardButton("🍪 Cookies",callback_data="cookies")]
        ]
        await q.edit_message_text("Choose type:",reply_markup=InlineKeyboardMarkup(buttons))

    elif q.data=="buy":
        await q.edit_message_text("Contact admin to buy points.")

    elif q.data=="accounts":
        buttons=[[InlineKeyboardButton(p,callback_data=f"acc_{p}")] for p in ACCOUNT_PLATFORMS]
        await q.edit_message_text("Select Platform:",reply_markup=InlineKeyboardMarkup(buttons))

    elif q.data=="cookies":
        buttons=[[InlineKeyboardButton(p,callback_data=f"cook_{p}")] for p in COOKIE_PLATFORMS]
        await q.edit_message_text("Select Cookie Platform:",reply_markup=InlineKeyboardMarkup(buttons))

    elif q.data.startswith("acc_"):
        platform=q.data[4:]
        if get_points(user_id)<POINT_COST:
            await q.edit_message_text("❌ Not enough points.")
            return
        item=deliver_account(platform)
        if not item:
            await q.edit_message_text("⚠️ Out of stock.")
            return
        update_points(user_id,-POINT_COST)
        log_transaction(user_id,"account",platform)
        await q.edit_message_text(f"Account:\n`{item}`",parse_mode="Markdown")

    elif q.data.startswith("cook_"):
        platform=q.data[5:]
        if get_points(user_id)<POINT_COST:
            await q.edit_message_text("❌ Not enough points.")
            return
        item=deliver_cookie(platform)
        if not item:
            await q.edit_message_text("⚠️ Out of stock.")
            return
        update_points(user_id,-POINT_COST)
        log_transaction(user_id,"cookie",platform)
        await q.edit_message_text(f"Cookie:\n`{item}`",parse_mode="Markdown")

# ================= RUN =================
app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()

