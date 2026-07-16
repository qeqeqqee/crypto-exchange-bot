import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# Admin
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Поддерживаемые пары криптовалют
SUPPORTED_PAIRS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "XRP": "XRPUSDT",
    "ADA": "ADAUSDT",
}

# Комиссия (в процентах)
EXCHANGE_COMMISSION = 1.5
