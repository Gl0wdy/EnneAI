import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEBUG_TOKEN = os.getenv("TELEGRAM_DEBUG_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")