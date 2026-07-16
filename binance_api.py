from config import SUPPORTED_PAIRS, RUB_TO_USD_RATE, EXCHANGE_COMMISSION
import random

# Список пар для имитации
SUPPORTED_PAIRS_LIST = list(SUPPORTED_PAIRS.keys())


def get_crypto_price(crypto):
    """Получить текущую цену криптовалюты"""
    if crypto in SUPPORTED_PAIRS:
        # Возвращаем базовую цену с небольшой случайной вариацией
        base_price = SUPPORTED_PAIRS[crypto]["price"]
        variation = base_price * random.uniform(-0.02, 0.02)  # ±2% вариация
        return base_price + variation
    return None


def get_all_prices():
    """Получить цены всех поддерживаемых криптовалют"""
    prices = {}
    for crypto in SUPPORTED_PAIRS:
        price = get_crypto_price(crypto)
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
    amount_usd = amount_rub / RUB_TO_USD_RATE
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
    
    price = get_crypto_price(crypto_type)
    if price is None:
        return False, "Не удалось получить цену криптовалюты"
    
    return True, "OK"
