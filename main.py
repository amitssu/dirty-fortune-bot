import asyncio
import random
import os
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("postgresql://postgres:IlCGUgrUfZKLQPAeRjwkOjPlpuUiavvB@postgres.railway.internal:5432/railway")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS fortunes (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL
        );
    """)
    await conn.close()

@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    user_input = inline_query.query.strip().lower()
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT text FROM fortunes ORDER BY RANDOM() LIMIT 1")
    await conn.close()
    if rows:
        fortune = rows[0]["text"]
    else:
        fortune = "Список предсказаний пуст."

    result = [
        InlineQueryResultArticle(
            id="1",
            title="Нажми, чтобы увидеть предсказание",
            input_message_content=InputTextMessageContent(fortune),
            description="Нажми, чтобы увидеть предсказание"
        )
    ]
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=0)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
