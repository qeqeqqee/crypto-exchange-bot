from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_SECRET_KEY, SUPPORTED_PAIRS
import asyncio
from functools import lru_cache

client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)


@lru_cache(maxsize=10)
def get_crypto_price(symbol):
    """Получить текущую цену криптовалюты в USDT"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"Ошибка при получении цены для {symbol}: {e}")
        return None


def get_all_prices():
    """Получить цены всех поддерживаемых криптовалют"""
    prices = {}
    for crypto, pair in SUPPORTED_PAIRS.items():
        price = get_crypto_price(pair)
        if price:
            prices[crypto] = price
    return prices


def calculate_exchange(amount_rub, price_usdt, commission_percent):
    """
    Рассчитать обмен рублей на крипто
    
    Args:
        amount_rub: Сумма в рублях
        price_usdt: Цена в USDT
        commission_percent: Процент комиссии
    
    Returns:
        dict с информацией об обмене
    """
    # Курс RUB/USD примерно 1 USD = 100 RUB (используйте реальный курс)
    usd_rate = 100  # Это упрощение, используйте реальный API для курса
    
    amount_usd = amount_rub / usd_rate
    commission = amount_usd * (commission_percent / 100)
    amount_after_commission = amount_usd - commission
    amount_crypto = amount_after_commission / price_usdt
    
    return {
        "amount_usd": amount_usd,
        "commission": commission,
        "amount_after_commission": amount_after_commission,
        "amount_crypto": amount_crypto
    }


def validate_order(amount_rub, crypto_type):
    """Проверить возможность обмена"""
    if amount_rub < 100:
        return False, "Минимальная сумма обмена: 100 рублей"
    
    if crypto_type not in SUPPORTED_PAIRS:
        return False, f"Криптовалюта {crypto_type} не поддерживается"
    
    price = get_crypto_price(SUPPORTED_PAIRS[crypto_type])
    if price is None:
        return False, "Не удалось получить цену криптовалюты"
    
    return True, "OK"
