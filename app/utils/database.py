import sqlite3
import os

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def commit(self):
        if self.conn:
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()


class TableCreator:
    def __init__(self, db: Database):
        self.db = db

    def create_orders_table(self):
        self.db.cursor.execute("""
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
            store INTEGER
        )
        """)
        self.db.commit()
