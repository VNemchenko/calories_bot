import os
from loguru import logger
import sys

logger.add(sys.stdout, format="{time} {level} {message}", level="DEBUG")


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HOST = os.getenv('HOST')
DATABASE = os.getenv('DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')