# config.py
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")

# ✅ Добавь проверку
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")
if not DB_URL:
    raise ValueError("DB_URL не найден в .env файле!")
if not PROVIDER_TOKEN:
    raise ValueError("PROVIDER_TOKEN не найден в .env файле!")