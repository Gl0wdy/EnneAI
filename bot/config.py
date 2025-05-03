from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEBUG_TOKEN = os.getenv('DEBUG_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

MAX_GROUP_HISTORY_LENGTH = 100