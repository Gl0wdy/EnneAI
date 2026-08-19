import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEBUG_TOKEN = os.getenv("TELEGRAM_DEBUG_TOKEN")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID"))

MONGO_URI = os.getenv('MONGO_URI')

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_PRIMARY_MODEL = 'nvidia/nemotron-3-super-120b-a12b:free'
OPENROUTER_SECONDARY_MODEL = 'nvidia/nemotron-3.5-lightning:free'