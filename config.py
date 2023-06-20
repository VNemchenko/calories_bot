import os
from loguru import logger
import sys
from datetime import datetime, timedelta

logger.add(sys.stdout, format="", level="INFO")


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HOST = os.getenv('HOST')
DATABASE = os.getenv('DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

FORM_URL = 'https://forms.gle/E4eePqeA6XXww3Pr5'
DONATE_URL = 'https://www.tinkoff.ru/cf/A5Sv53qqs89'


FOR_DATE = range(1)

WORDS_TO_DATES = {
        "сегодня": lambda: datetime.now().date(),
        "today": lambda: datetime.now().date(),
        "вчера": lambda: (datetime.now() - timedelta(days=1)).date(),
        "yesterday": lambda: (datetime.now() - timedelta(days=1)).date(),
        "позавчера": lambda: (datetime.now() - timedelta(days=2)).date()
    }
