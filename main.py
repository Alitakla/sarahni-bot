"""
بوت "صارحني" - بوت صراحة مجهول على تلغرام
كل مستخدم بياخد لينك خاص، وأي حدا يدخل عليه يقدر يبعتله رسالة مجهولة.
"""

import logging
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

DB_PATH = "sarahni.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pending (
            sender_id INTEGER PRIMARY KEY,
            target_id INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def set_pending(sender_id: int, target_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO pending (sender_id, target_id) VALUES (?, ?)",
        (sender_id, target_id),
    )
    conn.commit()
    conn.close()


def get_pending(sender_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT target_id FROM pending WHERE sender_id = ?", (sender_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def clear_pending(sender_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM pending WHERE sender_id = ?", (sender_id,))
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if args:
        try:
            target_id = int(args[0])
        except ValueError:
            await update.message.reply_text("اللينك غير صحيح.")
            return

        if target_id == user.id:
            await update.message.reply_text("ما بتقدر تصرح لحالك 😅")
            return

        set_pending(user.id, target_id)
        await update.message.reply_text(
            "اكتب رسالتك المجهولة هلأ وبوصل بدون اسمك ⬇️"
        )
    else:
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user.id}"
        await update.message.reply_text(
            "هاد لينكك الخاص، شاركه مع أصحابك حتى يصرحولك بشي بدون يحكوا اسمهم:\n\n"
            f"{link}",
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    target_id = get_pending(sender.id)

    if target_id is None:
        await update.message.reply_text(
            "ابعت /start حتى تاخد لينكك الخاص وتشاركه مع أصحابك."
        )
        return

    text = update.message.text

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📩 وصلتك صراحة جديدة:\n\n{text}",
        )
        await update.message.reply_text("تم إرسال صراحتك بنجاح ✅ (بشكل مجهول تماماً)")
    except Exception as e:
        logger.error(f"فشل إرسال الرسالة: {e}")
        await update.message.reply_text(
            "في مشكلة، ما قدرت أوصل الرسالة. تأكد إنه الشخص فتح محادثة مع البوت من قبل."
        )
    finally:
        clear_pending(sender.id)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing!")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("البوت شغال...")
    app.run_polling()


if __name__ == "__main__":
    main()
