import os
from loguru import logger
import sys
from datetime import datetime, timedelta


if os.getenv('LOG_ENV') == "stage":
    logger.add(sys.stdout, format="", level="INFO")
else:
    logger.add(f"/app/logs/calories_bot.log", rotation="3 day", format="{time} {level} {message}", level="INFO")

logger.add("/app/logs/special_calories.log", format="{time} {level} {message}", level="INFO", filter=lambda record: record["extra"].get("special"))


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')
HOST = os.getenv('HOST')
DATABASE = os.getenv('DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

FORM_URL = 'https://forms.gle/E4eePqeA6XXww3Pr5'


FOR_DATE = range(1)
RATE_LIMIT = int(os.getenv('RATE_LIMIT'))
SECRET_WORD = os.getenv('SECRET_WORD')

DIALOGFLOW_API_KEY = {
    "type": "service_account",
    "project_id": os.getenv('GOOGLE_PROJECT_ID'),
    "private_key_id": os.getenv('PRIVATE_KEY_ID'),
    "private_key": os.getenv('PRIVATE_KEY').replace('\\n', '\n').strip('"'),
    "client_email": os.getenv('CLIENT_EMAIL'),
    "client_id": os.getenv('CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('CERT_URL'),
    "universe_domain": "googleapis.com"
}

PROJECT_ID = os.getenv('PROJECT_ID')


WORDS_TO_DATES = {
        "сегодня": lambda: datetime.now().date(),
        "today": lambda: datetime.now().date(),
        "вчера": lambda: (datetime.now() - timedelta(days=1)).date(),
        "yesterday": lambda: (datetime.now() - timedelta(days=1)).date(),
        "позавчера": lambda: (datetime.now() - timedelta(days=2)).date()
    }

DATE_FORMATS = [r'\b\d{1,2}\.\d{1,2}\.\d{2}\b', r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',
                    r'\b\d{1,2}\s\w+\s\d{4}\b', r'\b\d{1,2}\s\w+\s\d{2}\b',
                    r'\b\d{1,2}\.\d{1,2}\b', r'\b\d{1,2}\s\w+\b']
INSTRUCT = f'Вы можете написать простым текстом то, что вы только что поели, и бот сохранит эти данные в базу, обновляя их с каждым сообщением. Вы можете запросить итоговые данные, введя соответствующую дату. Так же вы можете добавить пропущенный прием пищи, воспользовавшись командой в меню или введя /for_date. Будем рады отзывам и предложениям!'
START_MESSAGE = 'Привет! Давайте начнём отслеживание калорий. Просто сообщайте мне, что вы съели, чтобы не забывать. Если захотите увидеть общий подсчёт, отправьте дату в формате ДД.ММ.ГГ.'
