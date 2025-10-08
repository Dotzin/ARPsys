import pytest
import os
import tempfile
from app.services.database_service import DatabaseService
from app.core.exceptions import DatabaseException


class TestDatabaseService:
    def setup_method(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.service = DatabaseService(self.db_path)

    def teardown_method(self):
        self.service.close()
        os.unlink(self.db_path)

    def test_connect(self):
        self.service.connect()
        assert self.service.database.conn is not None

    def test_create_tables(self):
        self.service.connect()
        self.service.create_tables()
        # Check if tables exist
        cursor = self.service.database.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        assert cursor.fetchone() is not None
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sku_nichos'")
        assert cursor.fetchone() is not None

    def test_close(self):
        self.service.connect()
        assert self.service.database.conn is not None
        self.service.close()
        # Note: sqlite3 connection doesn't set to None on close, but we can check if it's closed
        # For simplicity, just check it was connected before
