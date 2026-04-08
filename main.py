import asyncio
import os
from datetime import date

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS fortunes (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            fortune_id INTEGER NOT NULL,
            used_on DATE NOT NULL
        );
    """)

    await conn.execute("ALTER TABLE usage_logs ADD COLUMN IF NOT EXISTS response_type TEXT;")
    await conn.execute("ALTER TABLE usage_logs ADD COLUMN IF NOT EXISTS stub_number INTEGER;")

    await conn.close()


def get_stub(n):
    if 3 <= n <= 5:
        return "Бот не покажет тебе предсказание до следующего дня."
    elif 35 <= n <= 39:
        return "Бот недоступен."
    elif 51 <= n <= 99:
        return "Бот не покажет тебе предсказание до следующего дня."
    elif n >= 100:
        return "Бот не покажет тебе предсказание до следующего дня."

    stubs = {
        2: "Ненасытный)",
        6: "Ты дурачок? Нет предсказаний, сказали же)",
        7: "Не напрашивайся, начинаешь раздражать 😅",
        8: "Отъебись.",
        9: "Пипец ты упёртый, но правда, хватит 🖐",
        10: "Ты тупой? Аня (@Annbd), забань его.",
        11: "Грёбаная демократия... не нашли возможности забанить тебя.",
        12: "Ань, пожалуйста, забань, а?",
        13: "Слышь, мы в России...",
        14: "Устал.",
        15: "Лох.",
        16: "Пид@р.",
        17: "Дитя коммунистического аборта.",
        18: "Товарищи ФСБ, заблокируйте ему интернет, плиз 🥺",
        19: "Ладно, ты выиграл!",
        20: "Вы занесены в чёрный список бота.",
    }

    return stubs.get(n, "Больше предсказаний на сегодня для тебя нет.")


@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    today = date.today()

    conn = await asyncpg.connect(DATABASE_URL)

    count_today = await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM usage_logs
        WHERE user_id = $1 AND used_on = $2
        """,
        user_id,
        today
    )

    if count_today > 0:
        stub_number = count_today + 1
        text = get_stub(stub_number)

        await conn.execute(
            """
            INSERT INTO usage_logs (user_id, fortune_id, used_on, response_type, stub_number)
            VALUES ($1, 0, $2, 'stub', $3)
            """,
            user_id,
            today,
            stub_number
        )

        await conn.close()

        result = [
            InlineQueryResultArticle(
                id="stub",
                title="😈 Ну-ну...",
                input_message_content=InputTextMessageContent(message_text=text)
            )
        ]

        await bot.answer_inline_query(inline_query.id, results=result, cache_time=0)
        return

    fortune_row = await conn.fetchrow(
        """
        SELECT id, text
        FROM fortunes
        WHERE is_active = TRUE
          AND id NOT IN (
              SELECT fortune_id
              FROM usage_logs
              WHERE used_on = $1
          )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        today,
    )

    if not fortune_row:
        await conn.close()

        result = [
            InlineQueryResultArticle(
                id="no_fortunes_left_today",
                title="На сегодня предсказания закончились",
                input_message_content=InputTextMessageContent(
                    message_text="🔮 На сегодня уникальные предсказания закончились. Возвращайся завтра."
                ),
            )
        ]

        await bot.answer_inline_query(inline_query.id, results=result, cache_time=0)
        return

    fortune_id = fortune_row["id"]
    fortune_text = fortune_row["text"]

    await conn.execute(
        """
        INSERT INTO usage_logs (user_id, fortune_id, used_on, response_type)
        VALUES ($1, $2, $3, 'fortune')
        """,
        user_id,
        fortune_id,
        today,
    )

    await conn.close()

    result = [
        InlineQueryResultArticle(
            id=f"fortune_{fortune_id}_{user_id}_{today.isoformat()}",
            title="Нажми, чтобы узнать свою судьбу",
            input_message_content=InputTextMessageContent(
                message_text=fortune_text
            ),
        )
    ]

    await bot.answer_inline_query(inline_query.id, results=result, cache_time=0)


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
