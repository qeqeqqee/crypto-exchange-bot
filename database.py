import aiosqlite
from config import DATABASE_URL
from datetime import datetime

DB_PATH = DATABASE_URL.replace("sqlite:///", "")


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                balance REAL DEFAULT 0
            )
        """)

        # Таблица транзакций
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                crypto_type TEXT,
                amount_rub REAL,
                amount_crypto REAL,
                price REAL,
                commission REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)

        await db.commit()


async def add_user(user_id, username):
    """Добавить нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()


async def get_user_balance(user_id):
    """Получить баланс пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0


async def add_transaction(user_id, crypto_type, amount_rub, amount_crypto, price, commission):
    """Добавить транзакцию"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO transactions (user_id, crypto_type, amount_rub, amount_crypto, price, commission, status)
            VALUES (?, ?, ?, ?, ?, ?, 'completed')
        """, (user_id, crypto_type, amount_rub, amount_crypto, price, commission))
        await db.commit()


async def get_user_transactions(user_id, limit=10):
    """Получить транзакции пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT crypto_type, amount_rub, amount_crypto, price, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        return await cursor.fetchall()
