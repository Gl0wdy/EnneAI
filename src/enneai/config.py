import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEBUG_TOKEN = os.getenv("TELEGRAM_DEBUG_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

MONGO_URI = os.getenv('MONGO_URI')

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")