from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

BASE_PATH = Path(__file__).resolve().parent
API_KEYS = os.getenv('API_KEYS')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEBUG_TOKEN=os.getenv('DEBUG_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
QDRANT_URL = os.getenv('QDRANT_URL')
MONGO_URL = os.getenv('MONGO_URL')