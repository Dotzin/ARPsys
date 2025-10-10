import sqlite3
import logging
from threading import Lock
from typing import Dict, Type, Any, Optional
from app.core.exceptions import DatabaseException


class SingletonMeta(type):
    _instances: Dict[Type[Any], Any] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Database inicializado com o caminho: {self.db_path}")

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.logger.info("Conexão com o banco de dados estabelecida")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao conectar ao banco de dados: {e}")
            raise DatabaseException(f"Failed to connect to database: {e}") from e

    @property
    def cursor(self):
        if self.conn is None:
            self.connect()
        return self.conn.cursor()

    def commit(self):
        try:
            if self.conn is None:
                self.connect()
            self.conn.commit()
            self.logger.info("Commit realizado com sucesso")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao executar commit: {e}")
            raise DatabaseException(f"Failed to commit database transaction: {e}") from e

    def close(self):
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.logger.info("Conexão com o banco de dados fechada")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao fechar conexão com o banco de dados: {e}")
            raise DatabaseException(f"Failed to close database connection: {e}") from e

    def get_all_user_ids(self):
        try:
            cursor = self.cursor
            cursor.execute("SELECT id FROM users")
            user_ids = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"Recuperados {len(user_ids)} IDs de usuários: {user_ids}")
            return user_ids
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao recuperar IDs de usuários: {e}")
            raise DatabaseException(f"Failed to get user IDs: {e}") from e


class TableCreator:
    def __init__(self, database: Database):
        self.database = database
        self.logger = logging.getLogger(__name__)

    def create_orders_table(self):
        try:
            self.database.cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    cart_id TEXT,
                    ad TEXT,
                    sku TEXT,
                    title TEXT,
                    quantity INTEGER,
                    total_value REAL,
                    payment_date TEXT,
                    status TEXT,
                    cost REAL DEFAULT 0,
                    gross_profit REAL DEFAULT 0,
                    taxes REAL DEFAULT 0,
                    freight REAL DEFAULT 0,
                    committee REAL DEFAULT 0,
                    fraction REAL DEFAULT 1,
                    profitability REAL DEFAULT 0,
                    rentability REAL DEFAULT 0,
                    store TEXT,
                    profit REAL DEFAULT 0,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(order_id, user_id)
                )
            """)
            self.database.commit()
            self.logger.info("Tabela orders criada/verificada")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao criar tabela orders: {e}")
            raise DatabaseException(f"Failed to create orders table: {e}") from e

    def create_sku_nichos_table(self):
        try:
            self.database.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sku_nichos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    sku TEXT UNIQUE,
                    nicho TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.database.commit()
            self.logger.info("Tabela sku_nichos criada/verificada")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao criar tabela sku_nichos: {e}")
            raise DatabaseException(f"Failed to create sku_nichos table: {e}") from e

    def create_users_table(self):
        try:
            self.database.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    api_session_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.database.commit()
            self.logger.info("Tabela users criada/verificada")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao criar tabela users: {e}")
            raise DatabaseException(f"Failed to create users table: {e}") from e

    def create_integrations_table(self):
        try:
            self.database.cursor.execute("""
                CREATE TABLE IF NOT EXISTS integrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    integration_type TEXT NOT NULL,
                    token_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            self.database.commit()
            self.logger.info("Tabela integrations criada/verificada")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao criar tabela integrations: {e}")
            raise DatabaseException(f"Failed to create integrations table: {e}") from e

    def add_user_id_to_tables(self):
        try:
            # Add user_id column to orders table if it doesn't exist
            cursor = self.database.cursor
            cursor.execute("PRAGMA table_info(orders)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'user_id' not in columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER")
                self.logger.info("Coluna user_id adicionada à tabela orders")

            # Add user_id column to sku_nichos table if it doesn't exist
            cursor = self.database.cursor
            cursor.execute("PRAGMA table_info(sku_nichos)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'user_id' not in columns:
                cursor.execute("ALTER TABLE sku_nichos ADD COLUMN user_id INTEGER")
                self.logger.info("Coluna user_id adicionada à tabela sku_nichos")



            self.database.commit()
            self.logger.info("Colunas user_id adicionadas/verificada nas tabelas")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao adicionar coluna user_id: {e}")
            raise DatabaseException(f"Failed to add user_id column: {e}") from e
