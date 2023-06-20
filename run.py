import re

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
        context.bot.send_message(chat_id=update.effective_chat.id, text='Привет, начнем подсчет калорий! Просто пиши то, что ты поел, чтобы не забыть, а если захочешь узнать итог, отправь дату в формате ДД.ММ.ГГ')


def process_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text

    if re.search(r'\b\d{2}\.\d{2}\.\d{2}\b', message_text):
        logger.info(f'function process_message started with date founded in  {message_text=}')
        data = get_data_from_db(user_id, message_text)
        context.bot.send_message(chat_id=update.effective_chat.id, text=data)
    else:
        json_data = get_nutrition_info(message_text)
        if json_data:
            message = add_entry(user_id, json_data)
        else:
            message = f'Извините, не удалось подсчитать калории, попробуйте сформулировать фразу иначе'

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
