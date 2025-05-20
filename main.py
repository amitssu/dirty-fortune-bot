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
     "Сегодня ты либо найдёшь любовь, либо снова уснёшь с телефоном в руке и рукой в штанах.",
    "Будущее туманно. Особенно после трёх рюмок и звонка бывшей.",
    "Сегодня ты будешь на высоте. Особенно если сядешь на кактус.",
    "Судьба тебе улыбается. Правда, с ухмылкой и битой в руке.",
    "Не плачь, дядя Ярослав добавит тебя в список на волейбол.",
    "Если чувствуешь себя так себе, напиши Амиру — он скинет тебе гифку.",
    "Сегодня тебе предстоит спорить с Прохором😥.",
    "Ты особенный. Как сообщение от банка в 3 часа ночи.",
    "Даже твоя тень сегодня от тебя отвернулась. Уважительно.",
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
