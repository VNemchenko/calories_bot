import os
from loguru import logger
import sys
from datetime import datetime, timedelta


if os.getenv('LOG_ENV') == "stage":
    logger.add(sys.stdout, format="", level="INFO")
else:
    logger.add(f"/app/logs/calories_bot.log", rotation="3 day", format="{time} {level} {message}", level="INFO")


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HOST = os.getenv('HOST')
DATABASE = os.getenv('DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

FORM_URL = 'https://forms.gle/E4eePqeA6XXww3Pr5'


FOR_DATE = range(1)
RATE_LIMIT = int(os.getenv('RATE_LIMIT'))
SECRET_WORD = os.getenv('SECRET_WORD')

WORDS_TO_DATES = {
        "сегодня": lambda: datetime.now().date(),
        "today": lambda: datetime.now().date(),
        "вчера": lambda: (datetime.now() - timedelta(days=1)).date(),
        "yesterday": lambda: (datetime.now() - timedelta(days=1)).date(),
        "позавчера": lambda: (datetime.now() - timedelta(days=2)).date()
    }
