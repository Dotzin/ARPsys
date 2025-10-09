import os
import sqlite3
import pandas as pd
import logging
from utils.ml_utils import train_ml_model

logger = logging.getLogger(__name__)

# Absolute path to DB
db_path = os.path.abspath("database.db")
logger.info(f"Absolute DB path being opened: {db_path}")

# Connect to DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if 'orders' table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
logger.info(f"Existing tables in DB: {tables}")

if "orders" not in tables:
    raise RuntimeError("The 'orders' table does not exist in the DB being opened!")

# Fetch orders with join on niches
query = """
SELECT o.*, n.nicho
FROM orders o
LEFT JOIN sku_nichos n ON o.sku = n.sku
"""
df_orders = pd.read_sql(query, conn)

# Check if there are records
if df_orders.empty:
    raise ValueError("There are no orders with niches to train the model.")

# Train the model
model = train_ml_model(df_orders)
logger.info("Model trained successfully and saved in models/sales_forecast_model.pkl")
