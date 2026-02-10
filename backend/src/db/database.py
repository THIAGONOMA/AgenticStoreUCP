"""Gerenciador de conexao com banco de dados SQLite."""
import aiosqlite
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from ..config import settings


class Database:
    """Gerenciador de conexoes SQLite."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Conectar ao banco."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
    
    async def disconnect(self):
        """Desconectar do banco."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    @property
    def connection(self) -> aiosqlite.Connection:
        """Obter conexao ativa."""
        if not self._connection:
            raise RuntimeError("Database not connected")
        return self._connection
    
    async def execute(self, query: str, params: tuple = ()):
        """Executar query."""
        async with self.connection.execute(query, params) as cursor:
            await self.connection.commit()
            return cursor
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """Buscar um registro."""
        async with self.connection.execute(query, params) as cursor:
            return await cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """Buscar todos os registros."""
        async with self.connection.execute(query, params) as cursor:
            return await cursor.fetchall()


# Instancias globais
products_db = Database(settings.products_db_path)
transactions_db = Database(settings.transactions_db_path)


@asynccontextmanager
async def get_products_db():
    """Context manager para banco de produtos."""
    await products_db.connect()
    try:
        yield products_db
    finally:
        await products_db.disconnect()


@asynccontextmanager
async def get_transactions_db():
    """Context manager para banco de transacoes."""
    await transactions_db.connect()
    try:
        yield transactions_db
    finally:
        await transactions_db.disconnect()


async def init_databases():
    """Inicializar bancos de dados com schemas."""
    # Products DB
    await products_db.connect()
    await products_db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            category TEXT,
            isbn TEXT UNIQUE,
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await products_db.execute("""
        CREATE INDEX IF NOT EXISTS idx_books_category ON books(category)
    """)
    await products_db.execute("""
        CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)
    """)
    
    # Discount codes
    await products_db.execute("""
        CREATE TABLE IF NOT EXISTS discount_codes (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            value INTEGER NOT NULL,
            min_purchase INTEGER DEFAULT 0,
            max_uses INTEGER,
            current_uses INTEGER DEFAULT 0,
            valid_from TIMESTAMP,
            valid_until TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)
    await products_db.disconnect()
    
    # Transactions DB
    await transactions_db.connect()
    await transactions_db.execute("""
        CREATE TABLE IF NOT EXISTS buyers (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await transactions_db.execute("""
        CREATE INDEX IF NOT EXISTS idx_buyers_email ON buyers(email)
    """)
    
    await transactions_db.execute("""
        CREATE TABLE IF NOT EXISTS checkout_sessions (
            id TEXT PRIMARY KEY,
            buyer_id TEXT,
            status TEXT DEFAULT 'draft',
            currency TEXT DEFAULT 'BRL',
            subtotal INTEGER DEFAULT 0,
            discount_total INTEGER DEFAULT 0,
            shipping_total INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES buyers(id)
        )
    """)
    
    await transactions_db.execute("""
        CREATE TABLE IF NOT EXISTS line_items (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            book_id TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,
            discount INTEGER DEFAULT 0,
            total INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES checkout_sessions(id)
        )
    """)
    await transactions_db.execute("""
        CREATE INDEX IF NOT EXISTS idx_line_items_session ON line_items(session_id)
    """)
    
    await transactions_db.execute("""
        CREATE TABLE IF NOT EXISTS applied_discounts (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            code TEXT NOT NULL,
            title TEXT NOT NULL,
            amount INTEGER NOT NULL,
            automatic INTEGER DEFAULT 0,
            allocation_path TEXT,
            FOREIGN KEY (session_id) REFERENCES checkout_sessions(id)
        )
    """)
    
    await transactions_db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            handler_id TEXT NOT NULL,
            token TEXT,
            mandate_jwt TEXT,
            status TEXT DEFAULT 'pending',
            amount INTEGER NOT NULL,
            processed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES checkout_sessions(id)
        )
    """)
    await transactions_db.disconnect()
    
    print("Databases initialized successfully!")
