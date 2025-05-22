import asyncio
import random
import os
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            text TEXT UNIQUE NOT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id BIGINT NOT NULL,
            prediction TEXT NOT NULL,
            timestamp BIGINT NOT NULL
        )
    """)
    await conn.close()

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Нажми: /fortune — чтобы получить предсказание.")

@dp.message(lambda message: message.text == "/fortune")
async def handle_fortune(message: types.Message):
    user_id = message.from_user.id
    now = int(time.time())
    conn = await asyncpg.connect(DATABASE_URL)

    # Проверим спам
    last = await conn.fetchrow("SELECT timestamp FROM user_activity WHERE user_id = $1 ORDER BY timestamp DESC LIMIT 1", user_id)
    if last and now - last["timestamp"] < 600:  # 10 минут
        await message.answer("Утали свой пыл! Ты уже получил своё предсказание.")
        await conn.close()
        return

    # Получим список всех предсказаний
    predictions = await conn.fetch("SELECT text FROM predictions")
    predictions = [row["text"] for row in predictions]

    # Исключим те, что уже были за последние 10 минут
    used = await conn.fetch("SELECT prediction FROM user_activity WHERE user_id = $1 AND timestamp > $2", user_id, now - 600)
    used_texts = {row["prediction"] for row in used}
    available = [p for p in predictions if p not in used_texts]

    if not available:
        available = predictions

    result = random.choice(available)
    await message.answer(result)
    await conn.execute("INSERT INTO user_activity (user_id, prediction, timestamp) VALUES ($1, $2, $3)", user_id, result, now)
    await conn.close()

@dp.inline_query()
async def inline_query(query: InlineQuery):
    input_content = InputTextMessageContent("Нажми, чтобы получить предсказание")
    item = InlineQueryResultArticle(
        id="1",
        title="Нажми, чтобы получить предсказание",
        input_message_content=input_content
    )
    await query.answer([item], cache_time=0)

async def on_startup():
    await init_db()

if __name__ == "__main__":
    asyncio.run(on_startup())
    dp.run_polling(bot)
