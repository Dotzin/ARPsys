import sqlite3
import pandas as pd
from utils.ml_utils import train_ml_model

# Conectar ao DB
conn = sqlite3.connect("database.db")

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
