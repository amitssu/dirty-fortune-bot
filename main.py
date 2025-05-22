import logging
import os
import random
import time
import sqlite3
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4

logging.basicConfig(level=logging.INFO)

DB_FILE = "botdata.db"
COOLDOWN_SECONDS = 600      # 10 минут
REPEAT_BLOCK_SECONDS = 604800  # Неделя
CLEANUP_INTERVAL = 86400    # Очистка раз в сутки
last_cleanup = 0

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fortunes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_time REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_fortunes (
            text TEXT PRIMARY KEY,
            used_time REAL
        )
    """)

    # Добавим фразы, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM fortunes")
    if cursor.fetchone()[0] == 0:
        sample_fortunes = [
            "Сегодня ты либо найдёшь любовь, либо снова уснёшь с телефоном в руке и рукой в штанах.",
            "Будущее туманно. Особенно после трёх рюмок и звонка бывшей.",
            "Сегодня ты будешь на высоте. Особенно если сядешь на кактус.",
            "Судьба тебе улыбается. Правда, с ухмылкой и битой в руке.",
            "Ты найдёшь опору. В чужом пахе. Случайно. (наверное)",
            "Ты станешь легендой. Как тот, кого ебали стоя, лёжа и в комментариях.",
            "Сегодня ты сияешь. Как пятно на трусах перед свиданием.",
            "Ты вдохновишь группу. На ритуальный отъеб с шаманскими плясками на твоих чувствах."
        ]
        cursor.executemany("INSERT INTO fortunes (text) VALUES (?)", [(f,) for f in sample_fortunes])
    conn.commit()
    conn.close()

def cleanup_db():
    global last_cleanup
    now = time.time()
    if now - last_cleanup >= CLEANUP_INTERVAL:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cooldowns WHERE last_time < ?", (now - 604800,))
        cursor.execute("DELETE FROM used_fortunes WHERE used_time < ?", (now - REPEAT_BLOCK_SECONDS))
        conn.commit()
        conn.close()
        last_cleanup = now

def user_can_receive(user_id):
    cleanup_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT last_time FROM cooldowns WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    now = time.time()
    if row and now - row[0] < COOLDOWN_SECONDS:
        conn.close()
        return False
    cursor.execute("REPLACE INTO cooldowns (user_id, last_time) VALUES (?, ?)", (user_id, now))
    conn.commit()
    conn.close()
    return True

def get_random_fortune():
    now = time.time()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM fortunes WHERE text NOT IN (SELECT text FROM used_fortunes)")
    available = [row[0] for row in cursor.fetchall()]

    if not available:
        cursor.execute("DELETE FROM used_fortunes")
        conn.commit()
        cursor.execute("SELECT text FROM fortunes")
        available = [row[0] for row in cursor.fetchall()]

    choice = random.choice(available)
    cursor.execute("REPLACE INTO used_fortunes (text, used_time) VALUES (?, ?)", (choice, now))
    conn.commit()
    conn.close()
    return choice

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.inline_query.from_user.id
    if user_can_receive(user_id):
        text = get_random_fortune()
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Такие себе пророчества",
            input_message_content=InputTextMessageContent(text),
            description="Нажми, чтобы увидеть предсказание",
        )
    else:
        text = "Угомонись! Ты уже получил своё пророчество. Вернись позже."
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Пыл поубавь...",
            input_message_content=InputTextMessageContent(text),
            description="Нажми, чтобы увидеть предсказание",
        )
    await update.inline_query.answer([result], cache_time=0)

if __name__ == "__main__":
    init_db()
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(InlineQueryHandler(inline_query))
    application.run_polling()
