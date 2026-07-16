import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# Admin
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Поддерживаемые пары криптовалют (с примерными ценами для тестирования)
SUPPORTED_PAIRS = {
    "BTC": {"name": "Bitcoin", "price": 45000},
    "ETH": {"name": "Ethereum", "price": 2500},
    "BNB": {"name": "Binance Coin", "price": 600},
    "XRP": {"name": "Ripple", "price": 2.5},
    "ADA": {"name": "Cardano", "price": 1.2},
}

# Комиссия (в процентах)
EXCHANGE_COMMISSION = 1.5

# Курс RUB/USD для тестирования
RUB_TO_USD_RATE = 100  # 1 USD = 100 RUB (примерно)
