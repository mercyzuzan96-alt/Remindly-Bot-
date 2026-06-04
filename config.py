import os

class Config:
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'bot_database.db')
