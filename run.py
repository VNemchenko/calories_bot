import re
import dateparser

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler, PreCheckoutQueryHandler

from config import TELEGRAM_BOT_TOKEN, logger, FOR_DATE, datetime, WORDS_TO_DATES, FORM_URL,RATE_LIMIT, SECRET_WORD, PROVIDER_TOKEN, DATE_FORMATS, INSTRUCT,START_MESSAGE
from chatgpt_utils import get_nutrition_info
from sql import (get_data_from_db, add_entry, reset_block_and_counter, is_user_vip, make_user_vip,
                 get_user, add_user, update_payment_date, get_user_position, requests_count)


def feedback(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Пожалуйста, оставьте свои отзывы и пожелания здесь: {FORM_URL}')


def donate(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    title = "Пожертвование"
    description = "Поддержите разработчика"
    payload = "Calories-Payload"  # this is optional
    provider_token = PROVIDER_TOKEN
    currency = "RUB"
    prices = [LabeledPrice("На оплату сервисов и развитие функционала", 20000)]
    context.bot.send_invoice(chat_id, title, description, payload, provider_token, currency, prices)
    # context.bot.send_invoice(chat_id, title, description, payload, provider_token, currency, prices, start_parameter=None, photo_url=None, photo_size=None, photo_width=None, photo_height=None, need_name=None, need_phone_number=None, need_email=None, need_shipping_address=None, is_flexible=None, disable_notification=None, reply_to_message_id=None, reply_markup=None, provider_data=None, send_phone_number_to_provider=None, send_email_to_provider=None, timeout=None, api_kwargs=None, allow_sending_without_reply=None, max_tip_amount=None, suggested_tip_amounts=None)


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload != 'Calories-Payload':
        logger.info(f"precheckout_callback fail {query.invoice_payload=}")
        context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                              error_message="Что-то пошло не так...")
    else:
        context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)


def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    successful_payment = update.message.successful_payment
    transaction_id = successful_payment.provider_payment_charge_id
    logger.info(f"Payment successful! Transaction ID: {transaction_id} from {user_id=}")
    update_payment_date(user_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Спасибо за поддержку!")


def champ(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    get_user_position(user_id)
    update.message.reply_text(get_user_position(user_id))


def instruct(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(INSTRUCT)


def start_for_vip(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Скажите волшебное слово")
    return FOR_DATE


def iddqd(update: Update, context: CallbackContext) -> int:
    message_text = update.message.text
    if message_text == SECRET_WORD:
        user_id = update.effective_user.id
        logger.info(f'function iddqd started with {user_id=}')
        make_user_vip(user_id)
        context.bot.send_message(chat_id=update.effective_chat.id, text='ГОТОВО, хе-хе-хе=))')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Другое слово')
    return ConversationHandler.END


def extract_date_from_message(message_text: str):
    date_obj = None
    for date_format in DATE_FORMATS:
        search = re.search(date_format, message_text)
        if search:
            date_str = search.group(0)
            datetime_obj = dateparser.parse(date_str, languages=['en', 'ru'])
            if datetime_obj:
                date_obj = datetime_obj.date()
                break
    if not date_obj:
        for word in message_text.split():
            if word.lower() in WORDS_TO_DATES:
                date_obj = WORDS_TO_DATES[word.lower()]()
                logger.info(f'function extract_date_from_message change {word=} to {date_obj=} with type {type(date_obj)}')
                break
    return date_obj


def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    logger.info(f'function start started with {user_id=}')
    user = get_user(user_id)
    if not user:
        add_user(user_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text=START_MESSAGE)


def start_for_date(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Отправьте сообщение в виде {день} {продукты}")
    return FOR_DATE


def process_for_date(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    message_text = update.message.text
    date_obj = extract_date_from_message(message_text)
    logger.info(f'processing message: {message_text} from user {user_id} with {date_obj=}')
    try:
        if date_obj:
            if requests_count(user_id) <= RATE_LIMIT:
                json_data = get_nutrition_info(message_text)
                message = add_entry(user_id, json_data, date_obj)
            else:
                message = f'Извините, вы превысили лимит запросов на сегодня'
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Дата не распознана. Пожалуйста, используйте формат ДД.ММ.ГГ или ключевые слова: сегодня, вчера, позавчера.")
        return ConversationHandler.END
    except Exception as e:
        logger.info(f'error in process_for_date: {e}')
        context.bot.send_message(chat_id=update.effective_chat.id, text='Не получилось внести данные. Попробуйте написать по-другому или введите команду /cancel')
        return FOR_DATE


def cancel(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выход из команды.")
    return ConversationHandler.END


def process_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text
    date_obj = extract_date_from_message(message_text)
    logger.info(f'processing message: {message_text} from user {user_id} with {date_obj=}')
    if date_obj:
        data = get_data_from_db(user_id, date_obj)
        context.bot.send_message(chat_id=update.effective_chat.id, text=data)
    else:
        if False and not is_user_vip(user_id):
            logger.info(f'user {user_id=} has 7 days use')
            message = 'Здорово, вы пользуетесь помощью бота уже больше недели! Как вам? Если вам нравится этот сервис, задонатьте пожалуйста на сопутствующие расходы.'
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
            donate(update, context)
        elif requests_count(user_id) <= RATE_LIMIT:
            try:
                date = datetime.now().date()
                json_data = get_nutrition_info(message_text)
                message = add_entry(user_id, json_data, date)
            except Exception as e:
                logger.error(f'Error from chatgpt_utils {e}')
                message = f'К сожалению, не получилось рассчитать калорийность. Попробуйте описать продукты иначе, или, если это напиток, укажите его калорийность, и я подсчитаю содержание углеводов.'
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            message = f'Извините, вы превысили лимит запросов на сегодня'
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
    dispatcher.add_handler(CommandHandler("feedback", feedback))
    dispatcher.add_handler(CommandHandler("donate", donate))
    dispatcher.add_handler(CommandHandler("instruct", instruct))
    dispatcher.add_handler(CommandHandler("champ", champ))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('for_date', start_for_date)],
        states={
            FOR_DATE: [MessageHandler(Filters.text & ~Filters.command, process_for_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    vip_handler = ConversationHandler(
        entry_points=[CommandHandler('become_vip', start_for_vip)],
        states={
            FOR_DATE: [MessageHandler(Filters.text & ~Filters.command, iddqd)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(vip_handler)

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    reset_block_and_counter()
    main()
