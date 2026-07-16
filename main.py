import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from config import TELEGRAM_BOT_TOKEN, SUPPORTED_PAIRS, EXCHANGE_COMMISSION
from database import init_db, add_user, get_user_balance, add_transaction, get_user_transactions
from binance_api import get_all_prices, calculate_exchange, validate_order, get_crypto_price, SUPPORTED_PAIRS as PAIRS

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot и Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# FSM States для обмена
class ExchangeState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_crypto = State()
    confirm_exchange = State()


# Главная клавиатура
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💱 Обменять")],
            [KeyboardButton(text="📊 Курсы"), KeyboardButton(text="📈 История")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True
    )
    return keyboard


def get_crypto_keyboard():
    """Клавиатура с криптовалютами"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=crypto) for crypto in list(SUPPORTED_PAIRS.keys())[:3]]],
        resize_keyboard=True
    )
    return keyboard


# ========== КОМАНДЫ ==========

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    await add_user(user_id, username)
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я бот для обмена рублей на криптовалюту через Binance.\n\n"
        f"Мои основные функции:\n"
        f"💱 Обменять рубли на крипто\n"
        f"📊 Смотреть текущие курсы\n"
        f"📈 История ваших транзакций\n\n"
        f"Выберите действие:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    await message.answer(
        "ℹ️ **Справка по использованию:**\n\n"
        "💱 **Обменять** - начать обмен рублей на крипто\n"
        "📊 **Курсы** - показать текущие курсы криптовалют\n"
        "📈 **История** - ваши последние транзакции\n"
        "👤 **Профиль** - информация о вашем аккаунте\n\n"
        "**Минимальная сумма обмена:** 100 рублей\n"
        "**Комиссия:** " + str(EXCHANGE_COMMISSION) + "%",
        parse_mode="Markdown"
    )


# ========== ОСНОВНЫЕ ФУНКЦИИ ==========

@dp.message(F.text == "💱 Обменять")
async def exchange_start(message: types.Message, state: FSMContext):
    """Начать процесс обмена"""
    await message.answer(
        "Введите сумму в рублях (минимум 100 РУБ):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ExchangeState.waiting_for_amount)


@dp.message(ExchangeState.waiting_for_amount)
async def exchange_get_amount(message: types.Message, state: FSMContext):
    """Получить сумму от пользователя"""
    try:
        amount = float(message.text)
        if amount < 100:
            await message.answer("Минимальная сумма: 100 рублей. Попробуйте снова:")
            return
        
        await state.update_data(amount_rub=amount)
        await message.answer(
            "Выберите криптовалюту:",
            reply_markup=get_crypto_keyboard()
        )
        await state.set_state(ExchangeState.waiting_for_crypto)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму:")


@dp.message(ExchangeState.waiting_for_crypto)
async def exchange_get_crypto(message: types.Message, state: FSMContext):
    """Получить выбор криптовалюты"""
    crypto = message.text.upper()
    
    if crypto not in SUPPORTED_PAIRS:
        await message.answer(f"Криптовалюта {crypto} не поддерживается. Выберите из списка:")
        return
    
    data = await state.get_data()
    amount_rub = data['amount_rub']
    
    # Получить цену
    price = get_crypto_price(PAIRS[crypto])
    if price is None:
        await message.answer("Не удалось получить цену. Попробуйте позже.")
        return
    
    # Рассчитать обмен
    exchange_info = calculate_exchange(amount_rub, price, EXCHANGE_COMMISSION)
    
    message_text = (
        f"📋 **Сумма обмена:**\n"
        f"Рубли: {amount_rub} РУБ\n"
        f"USD эквивалент: ${exchange_info['amount_usd']:.2f}\n"
        f"Комиссия: ${exchange_info['commission']:.2f}\n"
        f"К получению: ${exchange_info['amount_after_commission']:.2f}\n\n"
        f"💰 **Получите:**\n"
        f"{exchange_info['amount_crypto']:.6f} {crypto}\n"
        f"(Текущая цена: ${price:.2f})\n\n"
        f"Подтверждаете обмен?"
    )
    
    await state.update_data(
        crypto=crypto,
        price=price,
        amount_crypto=exchange_info['amount_crypto']
    )
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    
    await message.answer(message_text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(ExchangeState.confirm_exchange)


@dp.message(ExchangeState.confirm_exchange)
async def exchange_confirm(message: types.Message, state: FSMContext):
    """Подтвердить обмен"""
    if message.text == "✅ Подтвердить":
        data = await state.get_data()
        user_id = message.from_user.id
        
        # Сохранить транзакцию в БД
        await add_transaction(
            user_id,
            data['crypto'],
            data['amount_rub'],
            data['amount_crypto'],
            data['price'],
            data['amount_rub'] * (EXCHANGE_COMMISSION / 100)
        )
        
        # Информация о платеже
        invoice_text = (
            f"✅ **Обмен успешно зарегистрирован!**\n\n"
            f"📋 **Деталь транзакции:**\n"
            f"ID: {user_id}-{message.message_id}\n"
            f"Сумма: {data['amount_rub']} РУБ\n"
            f"Получите: {data['amount_crypto']:.6f} {data['crypto']}\n\n"
            f"💳 **Платеж:**\n"
            f"Перечислите {data['amount_rub']} РУБ на реквизиты\n"
            f"(реквизиты вашего счёта)\n\n"
            f"После подтверждения платежа крипто будет переведена на ваш адрес.\n"
            f"Введите адрес вашего кошелька {data['crypto']}:"
        )
        
        await message.answer(invoice_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        await state.clear()
    else:
        await message.answer("Обмен отменён.", reply_markup=get_main_keyboard())
        await state.clear()


@dp.message(F.text == "📊 Курсы")
async def show_prices(message: types.Message):
    """Показать текущие курсы"""
    prices = get_all_prices()
    
    if not prices:
        await message.answer("Не удалось получить курсы. Попробуйте позже.")
        return
    
    message_text = "📊 **Текущие курсы криптовалют:**\n\n"
    for crypto, price in prices.items():
        message_text += f"{crypto}: ${price:.2f}\n"
    
    message_text += f"\n💱 Комиссия: {EXCHANGE_COMMISSION}%"
    
    await message.answer(message_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@dp.message(F.text == "📈 История")
async def show_history(message: types.Message):
    """Показать историю транзакций"""
    user_id = message.from_user.id
    transactions = await get_user_transactions(user_id)
    
    if not transactions:
        await message.answer("У вас пока нет транзакций.", reply_markup=get_main_keyboard())
        return
    
    message_text = "📈 **Ваши последние транзакции:**\n\n"
    for i, (crypto, amount_rub, amount_crypto, price, created_at) in enumerate(transactions, 1):
        message_text += (
            f"{i}. {crypto}\n"
            f"   {amount_rub:.0f} РУБ → {amount_crypto:.6f} {crypto}\n"
            f"   Цена: ${price:.2f}\n"
            f"   Дата: {created_at}\n\n"
        )
    
    await message.answer(message_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    """Показать профиль пользователя"""
    user_id = message.from_user.id
    
    message_text = (
        f"👤 **Ваш профиль:**\n\n"
        f"ID: {user_id}\n"
        f"Имя: {message.from_user.first_name}\n"
        f"Username: @{message.from_user.username or 'не установлено'}\n\n"
        f"ℹ️ Для помощи введите /help"
    )
    
    await message.answer(message_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@dp.message(F.text == "ℹ️ Помощь")
async def help_button(message: types.Message):
    """Кнопка помощи"""
    await cmd_help(message)


# ========== ЗАПУСК БОТА ==========

async def main():
    """Главная функция"""
    await init_db()
    logger.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
