import re
from datetime import timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

from config import TELEGRAM_BOT_TOKEN, logger
from chatgpt_utils import get_nutrition_info
from sql import (get_data_from_db, add_entry,
                 get_user, add_user, update_payment_date, datetime)


def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    logger.info(f'function start started with {user_id=}')
    user = get_user(user_id)

    if user:
        last_payment_date = user['last_payment_date']
        if (datetime.now() - last_payment_date).days > 7:
            logger.info(f'user {user_id=} has 7 days use')
            keyboard = [[InlineKeyboardButton("Donate", callback_data='DONATE')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=update.effective_chat.id, text='Здорово, вы пользуетесь моей помощью уже неделю! Как вам? Если вам нравится этот сервис, задонатьте пожалуйста на оплату сервера')
    else:
        add_user(user_id)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Привет! Давайте начнём отслеживание калорий. Просто сообщайте мне, что вы съели, чтобы не забывать. Если захотите увидеть общий подсчёт, отправьте дату в формате ДД.ММ.ГГ.')


def process_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text

    # словарь для получения даты по ключевым словам
    words_to_dates = {
        "сегодня": lambda: datetime.now().date(),
        "today": lambda: datetime.now().date(),
        "вчера": lambda: (datetime.now() - timedelta(days=1)).date(),
        "yesterday": lambda: (datetime.now() - timedelta(days=1)).date(),
        "позавчера": lambda: (datetime.now() - timedelta(days=2)).date()
    }

    date_obj = None

    # проверка на наличие даты в формате dd.mm.yy
    if re.search(r'\b\d{2}\.\d{2}\.\d{2}\b', message_text):
        logger.info(f'function process_message started with date founded in  {message_text=}')
        date_obj = datetime.strptime(message_text, "%d.%m.%y").date()

    # проверка на наличие ключевых слов в сообщении
    else:
        for word in message_text.split():
            if word.lower() in words_to_dates:
                date_obj = words_to_dates[word.lower()]()
                break

    if date_obj:
        data = get_data_from_db(user_id, date_obj)
        context.bot.send_message(chat_id=update.effective_chat.id, text=data)
    else:
        try:
            json_data = get_nutrition_info(message_text)
            message = add_entry(user_id, json_data)
        except Exception as e:
            logger.error(f'Error from chatgpt_utils {e}')
            message = f'К сожалению, не получилось рассчитать калорийность. Попробуйте описать продукты иначе, или, если это напиток, укажите его калорийность, и я подсчитаю содержание углеводов.'

        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'DONATE':
        # here you should redirect user to payment page
        donate_process = True
        # after successful payment you should call update_payment_date function to update payment date for user
        if donate_process:
            update_payment_date(user_id)
            context.bot.send_message(chat_id=update.effective_chat.id, text="Спасибо!")


def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
