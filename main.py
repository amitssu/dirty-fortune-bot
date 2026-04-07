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

    await conn.close()


@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    today = date.today()

    conn = await asyncpg.connect(DATABASE_URL)

    existing_user_log = await conn.fetchrow(
        """
        SELECT fortune_id
        FROM usage_logs
        WHERE user_id = $1 AND used_on = $2
        LIMIT 1
        """,
        user_id,
        today,
    )

    if existing_user_log:
        await conn.close()

        result = [
            InlineQueryResultArticle(
                id="already_used_today",
                title="Ты уже получил предсказание сегодня",
                input_message_content=InputTextMessageContent(
                    message_text="🔒 Ты уже получил предсказание сегодня. Возвращайся завтра."
                ),
                description="Сегодня новое предсказание уже недоступно",
            )
        ]

        await bot.answer_inline_query(
            inline_query.id,
            results=result,
            cache_time=0,
            is_personal=True,
        )
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
                description="Сегодня новых уникальных предсказаний больше нет",
            )
        ]

        await bot.answer_inline_query(
            inline_query.id,
            results=result,
            cache_time=0,
            is_personal=True,
        )
        return

    fortune_id = fortune_row["id"]
    fortune_text = fortune_row["text"]

    await conn.execute(
        """
        INSERT INTO usage_logs (user_id, fortune_id, used_on)
        VALUES ($1, $2, $3)
        """,
        user_id,
        fortune_id,
        today,
    )

    await conn.close()

    result = [
        InlineQueryResultArticle(
            id=f"fortune_{fortune_id}_{user_id}_{today.isoformat()}",
            title="Нажми, чтобы увидеть предсказание",
            input_message_content=InputTextMessageContent(
                message_text=fortune_text
            ),
            description="Сегодняшнее уникальное предсказание",
        )
    ]

    await bot.answer_inline_query(
        inline_query.id,
        results=result,
        cache_time=0,
        is_personal=True,
    )


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
