from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
from dateutil.parser import parse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler, PreCheckoutQueryHandler

from config import TELEGRAM_BOT_TOKEN, logger, datetime, WORDS_TO_DATES, FORM_URL,RATE_LIMIT, PROVIDER_TOKEN, INSTRUCT,START_MESSAGE, DIALOGFLOW_API_KEY, PROJECT_ID
from chatgpt_utils import get_nutrition_info, get_food_smalltalk_answer
from sql import (get_data_from_db, add_entry, reset_block_and_counter,
                 get_user, add_user, update_payment_date, get_user_position, requests_count)

credentials = service_account.Credentials.from_service_account_info(DIALOGFLOW_API_KEY)
dialogflow_session_client = dialogflow.SessionsClient(credentials=credentials)


def get_date(date_obj) -> datetime.date:
    if not isinstance(date_obj, str):
        date_obj = date_obj[0]  # берем первый элемент из списка
    date_time_obj = parse(date_obj)
    return date_time_obj.date()


def feedback(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Пожалуйста, оставьте свои отзывы и пожелания здесь: {FORM_URL}')


def champ(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    get_user_position(user_id)
    update.message.reply_text(get_user_position(user_id))


def instruct(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(INSTRUCT)


def donate(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    title = "Пожертвование"
    description = "Поддержите разработчика"
    payload = "Calories-Payload"  # this is optional
    provider_token = ""
    currency = "XTR"
    prices = [LabeledPrice("На оплату сервисов и развитие функционала", 250)]
    response = context.bot.send_invoice(chat_id, title, description, payload, provider_token, currency, prices)
    logger.info(f"donate invoice sended {response.invoice=}")


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    logger.info(f"precheckout_callback start with {query=}")
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
    total_amount = successful_payment.total_amount
    currency = successful_payment.currency
    logger.info(f"Payment successful! Transaction ID: {transaction_id} from {user_id=}")
    logger.info(f"User {user_id} is donate {total_amount} {currency}", extra={"special": True})
    update_payment_date(user_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Спасибо за поддержку!")


def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(f'function start started with {user_id=}')
    user = get_user(user_id, chat_id)
    if not user:
        add_user(user_id, chat_id)
        logger.info(f"User {user_id} is joined", extra={"special": True})
    context.bot.send_message(chat_id=chat_id, text=START_MESSAGE)





def food_request_handler(update: Update, context: CallbackContext, entities) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text
    date_obj = datetime.now().date()

    logger.info(f'function food_request_handler started with {entities=}')
    if not entities['date-time']:
        for word in message_text.split():
            if word.lower() in WORDS_TO_DATES:
                date_obj = WORDS_TO_DATES[word.lower()]()
                logger.info(f'function food_request_handler change {word=} to {date_obj=} with type {type(date_obj)}')
                break
    else:
        date_obj = get_date(entities.get('date-time'))
    logger.info(f'processing message: {message_text} from user {user_id} with {date_obj=}')
    if requests_count(user_id) <= RATE_LIMIT:
        try:
            json_data = get_nutrition_info(message_text)
            if isinstance(json_data, str):
                message = json_data
            elif json_data:
                message = add_entry(user_id, json_data, date_obj)
            else:
                message = 'Ой, кажется, я не распознал никакой еды в сообщении, или вы хотели получить отчет, но я не понял. Пожалуйста, попробуйте использовать в вашей фразе слова "результат" или "итого"'
        except Exception as e:
            logger.error(f'Error from chatgpt_utils {e}')
            message = f'К сожалению, не получилось рассчитать калорийность. Попробуйте описать продукты иначе, или, если это напиток, укажите его калорийность, и я подсчитаю содержание углеводов.'
    else:
        message = f'Извините, вы превысили лимит запросов на сегодня'
        logger.info(f"User {user_id} is reach daily limit", extra={"special": True})
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def get_data_from_db_handler(update, context, entities):
    user_id = update.effective_user.id
    try:
        date_obj = get_date(entities.get('date-time'))
        logger.info(f'processing date request from user {user_id} with {date_obj=}')
        data = get_data_from_db(user_id, date_obj)
        context.bot.send_message(chat_id=update.effective_chat.id, text=data)
    except Exception as e:
        logger.info(f'error in get_data_from_db_handler: {e}')
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Не получилось извлечь данные. Попробуйте написать дату по-другому')


def food_smalltalk(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text
    logger.info(f'function food_smalltalk started with {message_text=}')
    if requests_count(user_id) <= RATE_LIMIT:
        try:
            message = get_food_smalltalk_answer(message_text)
        except Exception as e:
            logger.error(f'Error from chatgpt_utils {e}')
            message = f'Кажется, вас интересует вопрос по питанию. Сейчас эта функция в разработке, скоро я смогу отвечать на подобные вопросы.'
    else:
        message = f'Извините, вы превысили лимит запросов на сегодня'
        logger.info(f"User {user_id} is reach daily limit", extra={"special": True})
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def text_message_handler(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    session_id = f'telegram_{update.effective_user.id}'
    session = dialogflow_session_client.session_path(PROJECT_ID, session_id)
    text_input = dialogflow.types.TextInput(text=text, language_code='ru-RU')
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = dialogflow_session_client.detect_intent(session=session, query_input=query_input)
    intent = response.query_result.intent.display_name
    entities = dict(response.query_result.parameters)
    logger.info(f'text_message_handler start with {text=}, {intent=}, {entities=}')
    if intent == 'food_request':
        food_request_handler(update, context, entities)
    elif intent == 'report_for_date':
        get_data_from_db_handler(update, context, entities)
    elif intent == 'food_smalltalk':
        food_smalltalk(update, context)
    elif intent == 'donate':
        donate(update, context)
    elif intent == 'champ':
        champ(update, context)
    else:
        update.message.reply_text(response.query_result.fulfillment_text)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    # Команды
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("feedback", feedback))
    dispatcher.add_handler(CommandHandler("donate", donate))
    dispatcher.add_handler(CommandHandler("instruct", instruct))
    dispatcher.add_handler(CommandHandler("champ", champ))

    # Сообщения
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message_handler))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    reset_block_and_counter()
    main()
