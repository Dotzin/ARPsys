import os
import sqlite3
import pandas as pd
from utils.ml_utils import train_ml_model

# Caminho absoluto do DB
db_path = os.path.abspath("../database.db")
print(f"DB absoluto que estou abrindo: {db_path}")

# Conectar ao DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar se a tabela 'orders' existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print("Tabelas existentes no DB:", tables)

if "orders" not in tables:
    raise RuntimeError("A tabela 'orders' não existe no DB que estamos abrindo!")

# Buscar pedidos com join nos nichos
query = """
SELECT o.*, n.nicho
FROM orders o
LEFT JOIN sku_nichos n ON o.sku = n.sku
"""
df_orders = pd.read_sql(query, conn)

# Verificar se há registros
if df_orders.empty:
    raise ValueError("Não há pedidos com nichos para treinar o modelo.")

# Treinar o modelo
model = train_ml_model(df_orders)
print("Modelo treinado com sucesso e salvo em models/sales_forecast_model.pkl")
