import os
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from dotenv import load_dotenv

# بارگذاری تنظیمات از فایل .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DELETE_TIME = int(os.getenv("DELETE_TIME"))
DEFAULT_CAPTION = os.getenv("DEFAULT_CAPTION")

# اتصال به دیتابیس SQLite
conn = sqlite3.connect("files.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, file_id TEXT, caption TEXT)")
conn.commit()

# راه‌اندازی بات
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

# دکمه بررسی عضویت در کانال
def check_membership_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    keyboard.add(InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership"))
    return keyboard

# دریافت فایل از کاربر
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    file_id = message.document.file_id

    # ذخیره فایل در دیتابیس
    cursor.execute("INSERT INTO files (file_id, caption) VALUES (?, ?)", (file_id, DEFAULT_CAPTION))
    conn.commit()
    
    file_unique_id = message.document.file_unique_id
    download_link = f"https://t.me/{bot.username}?start={file_unique_id}"

    await message.reply(f"✅ فایل دریافت شد!\n📥 لینک دانلود شما:\n{download_link}")

# بررسی عضویت در کانال
async def is_user_member(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# دریافت فایل از لینک اختصاصی
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    args = message.get_args()
    
    if args:
        cursor.execute("SELECT file_id, caption FROM files WHERE rowid = ?", (args,))
        file = cursor.fetchone()

        if file:
            user_id = message.from_user.id
            if await is_user_member(user_id):
                sent_message = await bot.send_document(user_id, file[0], caption=file[1])
                await asyncio.sleep(DELETE_TIME)
                await bot.delete_message(user_id, sent_message.message_id)
            else:
                await message.reply("⚠️ برای دریافت فایل، ابتدا در کانال عضو شوید.", reply_markup=check_membership_keyboard())
        else:
            await message.reply("❌ فایل موردنظر یافت نشد.")
    else:
        await message.reply("سلام! فایل موردنظر خود را ارسال کنید.")

# بررسی عضویت بعد از کلیک روی دکمه
@dp.callback_query_handler(lambda call: call.data == "check_membership")
async def check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    if await is_user_member(user_id):
        await call.message.edit_text("✅ شما عضو کانال هستید. حالا می‌توانید فایل خود را دریافت کنید.")
    else:
        await call.answer("⚠️ هنوز عضو کانال نشده‌اید!", show_alert=True)

# اجرای ربات
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
