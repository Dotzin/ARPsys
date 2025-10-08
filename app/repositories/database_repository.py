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
        self.cursor: Optional[sqlite3.Cursor] = None
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Database inicializado com o caminho: {self.db_path}")

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.logger.info("Conexão com o banco de dados estabelecida")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao conectar ao banco de dados: {e}")
            raise DatabaseException(f"Failed to connect to database: {e}") from e

    def commit(self):
        try:
            assert self.conn is not None
            self.conn.commit()
            self.logger.info("Commit realizado com sucesso")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao executar commit: {e}")
            raise DatabaseException(f"Failed to commit database transaction: {e}") from e

    def close(self):
        try:
            if self.conn:
                self.conn.close()
                self.logger.info("Conexão com o banco de dados fechada")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao fechar conexão com o banco de dados: {e}")
            raise DatabaseException(f"Failed to close database connection: {e}") from e


class TableCreator:
    def __init__(self, db: Database):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.logger.info("TableCreator inicializado")

    def create_orders_table(self):
        try:
            self.logger.info("Criando tabela 'orders' se não existir")
            self.db.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                cart_id TEXT,
                ad TEXT,
                sku TEXT,
                title TEXT,
                quantity INTEGER,
                total_value REAL,
                payment_date TEXT,
                status TEXT,
                cost REAL,
                gross_profit REAL,
                taxes REAL,
                freight REAL,
                committee REAL,
                fraction REAL,
                profitability REAL,
                rentability REAL,
                store INTEGER,
                profit REAL
            )
            """
            )
            self.db.commit()
            self.logger.info("Tabela 'orders' criada ou já existente")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao criar tabela 'orders': {e}")
            raise DatabaseException(f"Failed to create orders table: {e}") from e

    def create_sku_nichos_table(self):
        try:
            self.logger.info("Criando tabela 'sku_nichos' se não existir")
            self.db.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS sku_nichos (
                sku TEXT PRIMARY KEY,
                nicho TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )
            self.db.commit()
            self.logger.info("Tabela 'sku_nichos' criada ou já existente")
        except sqlite3.Error as e:
            self.logger.exception(f"Erro ao criar tabela 'sku_nichos': {e}")
            raise DatabaseException(f"Failed to create sku_nichos table: {e}") from e
