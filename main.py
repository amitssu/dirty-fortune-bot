import logging
import os
import random
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4

# Включаем логгирование (по желанию)
logging.basicConfig(level=logging.INFO)

# Грязные предсказания
FORTUNES = [
    "Сегодня тебя ждёт… неприятность, но ты её не заметишь.",
    "Ты — не случайность. Ты — предупреждение.",
    "Завтра будет лучше. Или хуже. В любом случае, не надейся.",
    "Любовь рядом. Но ты ей не нравишься.",
    "Ты думаешь, ты особенный? Так вот — нет.",
    "Жди неожиданного. Особенно от себя.",
    "Будущее туманно. Как и твои шансы на успех.",
    "Сегодня ты в ударе! Особенно по морде.",
    "Жопа близко, но держись!",
    "День будет хорошим. Ну, как хорошим... Переживёшь.",
    "Кто-то на тебя сегодня наорёт. И будет прав.",
    "Судьба такая: или пан, или срал в кустах.",
    "Любовь найдёт тебя. Правда, это будет кот.",
    "Ничего не получится. Но весело будет!"
]

def get_random_fortune():
    return random.choice(FORTUNES)

# Обработчик инлайн-запросов
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query.strip()  # не важен, пусть даже пустой
    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title="Твоё грязное предсказание",
        input_message_content=InputTextMessageContent(get_random_fortune()),
    )
    await update.inline_query.answer([result], cache_time=0)

# Запуск приложения
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(InlineQueryHandler(inline_query))
    application.run_polling()
