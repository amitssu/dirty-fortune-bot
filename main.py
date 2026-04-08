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

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            id INTEGER PRIMARY KEY,
            current_cycle INTEGER NOT NULL DEFAULT 1
        );
    """)

    await conn.execute(
        "INSERT INTO bot_state (id, current_cycle) VALUES (1, 1) ON CONFLICT (id) DO NOTHING;"
    )

    await conn.execute("ALTER TABLE usage_logs ADD COLUMN IF NOT EXISTS response_type TEXT;")
    await conn.execute("ALTER TABLE usage_logs ADD COLUMN IF NOT EXISTS stub_number INTEGER;")
    await conn.execute("ALTER TABLE usage_logs ADD COLUMN IF NOT EXISTS cycle_number INTEGER;")

    await conn.close()


def get_stub(n: int) -> str:
    if 3 <= n <= 5:
        return "Бот не покажет тебе предсказание до следующего дня."

    if 35 <= n <= 39:
        return "Бот недоступен."

    if 51 <= n <= 99:
        return "Бот не покажет тебе предсказание до следующего дня."

    if n >= 101:
        return "Бот не покажет тебе предсказание до следующего дня."

    stubs = {
        1: "Больше предсказаний на сегодня для тебя нет.",
        2: "Ненасытный/ая)",
        6: "Ты дурачок/ра? Нет предсказаний, сказали же)",
        7: "Не напрашивайся, начинаешь раздражать 😅",
        8: "Отъебись.",
        9: "Пипец ты упёртый/ая, но правда, хватит 🖐",
        10: "Ты тупой/ая? Аня (@nnbd), забань его/её.",
        11: "Грёбаная демократия и либеральные права в этом чате — не нашли возможности забанить тебя. Сук...",
        12: "Ань, пожалуйста, забань, а?",
        13: "Слышь, мы в России. Когда-нибудь и сюда дойдут традиционные ценности и швабры в заднице.",
        14: "Устал/а.",
        15: "Лох/ушка.",
        16: "Пид@р/ка.",
        17: "Дитя коммунистического аборта.",
        18: "Товарищи ФСБ, заблокируйте ему/ей интернет, плиз 🥺",
        19: "Ладно, ты выиграл/а! 🥇🏆 Я больше не буду тебе отвечать.",
        20: "Вы занесены в чёрный список бота.",
        21: "Вы занесены в чёрный список бота.",
        22: "Вы занесены в чёрный список бота.",
        23: "Я клянусь, если ты ещё раз вызовешь меня, я солью твои нюдсы!",
        24: "Даю тебе три попытки на понимание, чтобы ты так больше не делал/а. Первую ты потерял/а!",
        25: "Дурачок/ра, блэт. Вторая попытка в помойке.",
        26: "Давай-давай. Третья попытка утеряна. Сделай ещё раз — и я скину твои нюдсы.",
        27: "Ну всё, доигрался/ась!\nhttps://i.pinimg.com/474x/87/95/8b/87958b29c6c1bd0bb626b12df303f6c6.jpg?nii=t",
        28: "Каждый раз, как ты будешь просить предсказание, я буду фапать на твои нюдсы.",
        29: "Извращенец/енка 🥸",
        30: "Получай в ебало.\nhttps://i.pinimg.com/736x/9a/d5/8d/9ad58dbbd80458ccef366f70c6f9fcd9.jpg",
        31: "Тебе че, внимания не хватает? Иди у родителей своих попроси.",
        32: "Господи! Помоги! Ты же видишь, я больше так не могу!",
        33: "Сатана, я продаю душу, но пусть меня больше не вызывают!",
        34: "Звуки плача 😢",
        40: "Ты.",
        41: "Ебобо.",
        42: "Думаю, тебе нужно обратиться к специалисту. Маньяк/чка!",
        43: "Ну шо, спасибо всем, кто это всё посмотрел. Надеюсь, вас это повеселило. Я благодарен/на человеку, благодаря которому мой труд не остался без внимания. Спасибо тебе!",
        44: "Пипец, жёстко. Как же ты засрал/а спамом то место, где получал/а все эти предсказания. Дальше ничего не будет.",
        100: "Пипец, жёстко. Как же ты засрал/а спамом то место, где получал/а все эти предсказания. Дальше ничего не будет.",
    }

    return stubs.get(n, "Бот не покажет тебе предсказание до следующего дня.")


async def get_or_rotate_fortune(conn: asyncpg.Connection):
    current_cycle = await conn.fetchval(
        "SELECT current_cycle FROM bot_state WHERE id = 1"
    )

    fortune_row = await conn.fetchrow(
        """
        SELECT id, text
        FROM fortunes
        WHERE is_active = TRUE
          AND id NOT IN (
              SELECT fortune_id
              FROM usage_logs
              WHERE response_type = 'fortune'
                AND cycle_number = $1
                AND fortune_id <> 0
          )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        current_cycle,
    )

    if fortune_row:
        return current_cycle, fortune_row

    active_count = await conn.fetchval(
        "SELECT COUNT(*) FROM fortunes WHERE is_active = TRUE"
    )

    if not active_count or active_count == 0:
        return current_cycle, None

    current_cycle += 1

    await conn.execute(
        "UPDATE bot_state SET current_cycle = $1 WHERE id = 1",
        current_cycle,
    )

    fortune_row = await conn.fetchrow(
        """
        SELECT id, text
        FROM fortunes
        WHERE is_active = TRUE
        ORDER BY RANDOM()
        LIMIT 1
        """
    )

    return current_cycle, fortune_row


@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    today = date.today()

    conn = await asyncpg.connect(DATABASE_URL)

    has_fortune_today = await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM usage_logs
        WHERE user_id = $1
          AND used_on = $2
          AND response_type = 'fortune'
        """,
        user_id,
        today,
    )

    if has_fortune_today and has_fortune_today > 0:
        stub_count_today = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM usage_logs
            WHERE user_id = $1
              AND used_on = $2
              AND response_type = 'stub'
            """,
            user_id,
            today,
        )

        # 2-й запрос дня -> заглушка 1
        # 3-й запрос дня -> заглушка 2
        stub_number = stub_count_today + 1
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
                id=f"stub_{user_id}_{today.isoformat()}_{stub_number}",
                title="😈 Ну-ну...",
                input_message_content=InputTextMessageContent(message_text=text),
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

    current_cycle, fortune_row = await get_or_rotate_fortune(conn)

    if not fortune_row:
        await conn.close()

        result = [
            InlineQueryResultArticle(
                id="no_fortunes_available",
                title="Предсказания недоступны",
                input_message_content=InputTextMessageContent(
                    message_text="🔮 В базе нет активных предсказаний."
                ),
                description="Сейчас активных предсказаний нет",
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
        INSERT INTO usage_logs (user_id, fortune_id, used_on, response_type, cycle_number)
        VALUES ($1, $2, $3, 'fortune', $4)
        """,
        user_id,
        fortune_id,
        today,
        current_cycle,
    )

    await conn.close()

    result = [
        InlineQueryResultArticle(
            id=f"fortune_{fortune_id}_{user_id}_{today.isoformat()}_{current_cycle}",
            title="Нажми, чтобы узнать свою судьбу",
            input_message_content=InputTextMessageContent(
                message_text=fortune_text
            ),
            description="Сегодняшнее предсказание",
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
