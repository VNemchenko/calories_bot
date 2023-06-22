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
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')
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

DATE_FORMATS = [r'\b\d{1,2}\.\d{1,2}\.\d{2}\b', r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',
                    r'\b\d{1,2}\s\w+\s\d{4}\b', r'\b\d{1,2}\s\w+\s\d{2}\b',
                    r'\b\d{1,2}\.\d{1,2}\b', r'\b\d{1,2}\s\w+\b']
INSTRUCT = f'Вы можете написать простым текстом то, что вы только что поели, и бот сохранит эти данные в базу, обновляя их с каждым сообщением. Вы можете запросить итоговые данные, введя соответствующую дату. Так же вы можете добавить пропущенный прием пищи, воспользовавшись командой в меню или введя /for_date. Будем рады отзывам и предложениям!'
START_MESSAGE = 'Привет! Давайте начнём отслеживание калорий. Просто сообщайте мне, что вы съели, чтобы не забывать. Если захотите увидеть общий подсчёт, отправьте дату в формате ДД.ММ.ГГ.'
