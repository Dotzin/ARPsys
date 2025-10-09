import pytest
import sqlite3
import os
import tempfile
from app.services.database_service import DatabaseService
from app.services.report_service import ReportService
from app.services.order_service import OrderInserter
from app.services.sku_nicho_service import SkuNichoInserter
from app.services.data_service import Data
from app.services.data_parser_service import DataParser


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_service(temp_db):
    """Create a database service with temporary database"""
    service = DatabaseService(temp_db)
    service.connect()
    service.create_tables()
    yield service
    service.close()


@pytest.fixture
def order_inserter(db_service):
    """Create an order inserter"""
    return OrderInserter(db_service.database)


@pytest.fixture
def sku_nicho_inserter(db_service):
    """Create a SKU/nicho inserter"""
    return SkuNichoInserter(db_service.database)


@pytest.fixture
def report_service(db_service):
    """Create a report service"""
    return ReportService(db_service.database)


def test_database_service_creation(db_service):
    """Test database service initialization"""
    assert db_service.database is not None
    assert db_service.database.conn is not None


def test_order_inserter_creation(order_inserter):
    """Test order inserter initialization"""
    assert order_inserter.db is not None


def test_sku_nicho_inserter_creation(sku_nicho_inserter):
    """Test SKU/nicho inserter initialization"""
    assert sku_nicho_inserter.db is not None


def test_report_service_creation(report_service):
    """Test report service initialization"""
    assert report_service.db is not None


def test_sku_nicho_insert_one(sku_nicho_inserter):
    """Test inserting a single SKU/nicho"""
    # Clear existing data
    sku_nicho_inserter.db.cursor.execute("DELETE FROM sku_nichos")
    sku_nicho_inserter.db.commit()
    sku_nicho_inserter.insert_one("TEST123", "Test Nicho")
    rows = sku_nicho_inserter.list_all()
    assert len(rows) == 1
    assert rows[0][0] == "TEST123"
    assert rows[0][1] == "Test Nicho"


def test_sku_nicho_insert_many(sku_nicho_inserter):
    """Test inserting multiple SKU/nicho records"""
    # Clear existing data
    sku_nicho_inserter.db.cursor.execute("DELETE FROM sku_nichos")
    sku_nicho_inserter.db.commit()
    data = [
        {"sku": "TEST456", "nicho": "Nicho 1"},
        {"sku": "TEST789", "nicho": "Nicho 2"},
    ]
    sku_nicho_inserter.insert_many(data)
    rows = sku_nicho_inserter.list_all()
    assert len(rows) == 2


def test_sku_nicho_update(sku_nicho_inserter):
    """Test updating a SKU's nicho"""
    # Clear existing data
    sku_nicho_inserter.db.cursor.execute("DELETE FROM sku_nichos")
    sku_nicho_inserter.db.commit()
    sku_nicho_inserter.insert_one("TEST123", "Old Nicho")
    result = sku_nicho_inserter.update_nicho("TEST123", "New Nicho")
    assert result == 1
    rows = sku_nicho_inserter.list_all()
    assert rows[0][1] == "New Nicho"


def test_sku_nicho_delete(sku_nicho_inserter):
    """Test deleting a SKU"""
    # Clear existing data
    sku_nicho_inserter.db.cursor.execute("DELETE FROM sku_nichos")
    sku_nicho_inserter.db.commit()
    sku_nicho_inserter.insert_one("TEST123", "Test Nicho")
    result = sku_nicho_inserter.delete_sku("TEST123")
    assert result == 1
    rows = sku_nicho_inserter.list_all()
    assert len(rows) == 0


def test_order_insert_single(order_inserter):
    """Test inserting a single order"""
    order_data = {
        "cart_id": "CART123",
        "order_id": "ORD123",
        "sku": "SKU123",
        "quantity": 2,
        "total_value": 100.0,
        "payment_date": "2024-01-01 10:00:00",
    }
    order_inserter.insert_orders(order_data)
    # Verify insertion by querying database
    cursor = order_inserter.db.cursor
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    assert count == 1


def test_order_insert_multiple(order_inserter):
    """Test inserting multiple orders"""
    orders_data = {
        "CART123": [
            {
                "order_id": "ORD123",
                "sku": "SKU123",
                "quantity": 2,
                "total_value": 100.0,
                "payment_date": "2024-01-01 10:00:00",
            },
            {
                "order_id": "ORD124",
                "sku": "SKU456",
                "quantity": 1,
                "total_value": 50.0,
                "payment_date": "2024-01-01 11:00:00",
            },
        ]
    }
    order_inserter.insert_orders(orders_data)
    cursor = order_inserter.db.cursor
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    assert count == 2


def test_report_service_get_daily_report(report_service):
    """Test getting daily report data"""
    # Clear existing data
    report_service.db.cursor.execute("DELETE FROM orders")
    report_service.db.commit()
    # Insert some test data first
    cursor = report_service.db.cursor
    cursor.execute(
        """
        INSERT INTO orders (order_id, sku, quantity, total_value, payment_date, profit)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        ("ORD123", "SKU123", 2, 100.0, "2024-01-01 10:00:00", 10.0),
    )
    report_service.db.commit()

    report = report_service.get_daily_report_data()
    # Report structure depends on data availability
    assert isinstance(report, dict)


def test_data_service():
    """Test data service for API calls"""
    # Mock URL and cookies
    data_service = Data("https://httpbin.org/json", {"test": "cookie"})
    assert data_service.url == "https://httpbin.org/json"
    assert data_service.cookies == {"test": "cookie"}


def test_data_parser():
    """Test data parser"""
    sample_data = [
        {
            "cart": "CART123",
            "order": "ORD123",
            "sku": "SKU123",
            "quantity": 2,
            "total_value": 100.0,
        }
    ]
    parser = DataParser(sample_data)
    parsed = parser.parse_orders()
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["cart_id"] == "CART123"
