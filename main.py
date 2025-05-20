
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4
import random
import os

PREDICTIONS = [
    "Сегодня ты в ударе! Особенно по морде.",
    "Жопа близко, но держись!",
    "День будет хорошим. Ну, как хорошим... Переживёшь.",
    "Кто-то на тебя сегодня наорёт. И будет прав.",
    "Судьба такая: или пан, или срал в кустах.",
    "Любовь найдёт тебя. Правда, это будет кот.",
    "Ничего не получится. Но весело будет!"
]

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Предсказание",
            input_message_content=InputTextMessageContent(random.choice(PREDICTIONS))
        )
    ]
    await update.inline_query.answer(results, cache_time=1)

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(InlineQueryHandler(inline_query_handler))
app.run_polling()
