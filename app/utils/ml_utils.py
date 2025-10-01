import pandas as pd
from joblib import dump, load
import lightgbm as lgb
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

MODEL_PATH = "models/sales_forecast_model.pkl"

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Extraindo features do dataframe")
    df = df.copy()
    df["payment_date"] = pd.to_datetime(df["payment_date"])
    df["day"] = df["payment_date"].dt.date
    df["hour"] = df["payment_date"].dt.hour
    df["weekday"] = df["payment_date"].dt.weekday
    df["month"] = df["payment_date"].dt.month

    logger.info("Calculando médias por SKU, nicho e loja")
    df["sku_avg_qty"] = df.groupby("sku")["quantity"].transform("mean")
    df["sku_avg_total"] = df.groupby("sku")["total_value"].transform("mean")
    df["sku_avg_profit"] = df.groupby("sku")["gross_profit"].transform("mean")

    df["nicho_avg_qty"] = df.groupby("nicho")["quantity"].transform("mean")
    df["nicho_avg_total"] = df.groupby("nicho")["total_value"].transform("mean")
    df["nicho_avg_profit"] = df.groupby("nicho")["gross_profit"].transform("mean")

    df["store_avg_qty"] = df.groupby("store")["quantity"].transform("mean")
    df["store_avg_total"] = df.groupby("store")["total_value"].transform("mean")
    df["store_avg_profit"] = df.groupby("store")["gross_profit"].transform("mean")

    logger.info("Features extraídas com sucesso")
    return df

def train_ml_model(df: pd.DataFrame):
    logger.info("Iniciando treinamento do modelo ML")
    df_feat = extract_features(df)
    df_feat = df_feat.sort_values(["sku", "payment_date"])
    df_feat["target_qty_next_day"] = df_feat.groupby("sku")["quantity"].shift(-1)
    df_train = df_feat.dropna(subset=["target_qty_next_day"])
    logger.info(f"{len(df_train)} registros disponíveis para treinamento")

    features = [
        "quantity", "total_value", "gross_profit", "cost", "freight", "taxes", "fraction",
        "sku_avg_qty", "sku_avg_total", "sku_avg_profit",
        "nicho_avg_qty", "nicho_avg_total", "nicho_avg_profit",
        "store_avg_qty", "store_avg_total", "store_avg_profit",
        "weekday", "hour", "month"
    ]
    X = df_train[features]
    y = df_train["target_qty_next_day"]

    model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05, num_leaves=31)
    model.fit(X, y)
    logger.info("Modelo treinado com sucesso")

    if not os.path.exists("models"):
        os.makedirs("models")
        logger.info("Pasta 'models' criada")
    dump(model, MODEL_PATH)
    logger.info(f"Modelo salvo em {MODEL_PATH}")
    return model

def predict_sales_for_df(df: pd.DataFrame):
    logger.info("Iniciando previsão de vendas")
    if not Path(MODEL_PATH).exists():
        logger.error("Modelo ML não encontrado. Execute train_ml_model() primeiro.")
        raise FileNotFoundError("Modelo ML não encontrado. Execute train_ml_model() primeiro.")

    model = load(MODEL_PATH)
    logger.info("Modelo ML carregado com sucesso")

    df_feat = extract_features(df)
    features = [
        "quantity", "total_value", "gross_profit", "cost", "freight", "taxes", "fraction",
        "sku_avg_qty", "sku_avg_total", "sku_avg_profit",
        "nicho_avg_qty", "nicho_avg_total", "nicho_avg_profit",
        "store_avg_qty", "store_avg_total", "store_avg_profit",
        "weekday", "hour", "month"
    ]
    X = df_feat[features]
    df_feat["forecast_qty_next_day"] = model.predict(X)
    logger.info("Previsão concluída para todos os registros")

    conclusions = []

    # Nicho
    top_nichos = df_feat.groupby("nicho")["forecast_qty_next_day"].sum().sort_values(ascending=False)
    if not top_nichos.empty:
        conclusions.append({"melhor_nicho_previsto": top_nichos.idxmax(), "quantidade_prevista": float(top_nichos.max())})
        logger.info(f"Melhor nicho previsto: {top_nichos.idxmax()} com {top_nichos.max()} unidades")

    # Produto
    top_produtos = df_feat.groupby("sku")["forecast_qty_next_day"].sum().sort_values(ascending=False)
    if not top_produtos.empty:
        conclusions.append({"melhor_produto_previsto": top_produtos.idxmax(), "quantidade_prevista": float(top_produtos.max())})
        logger.info(f"Melhor produto previsto: {top_produtos.idxmax()} com {top_produtos.max()} unidades")

    # Hora pico
    peak_hours = df_feat.groupby("hour")["forecast_qty_next_day"].sum().sort_values(ascending=False)
    if not peak_hours.empty:
        conclusions.append({"hora_pico_prevista": int(peak_hours.idxmax()), "quantidade_prevista": float(peak_hours.max())})
        logger.info(f"Hora pico prevista: {int(peak_hours.idxmax())} com {peak_hours.max()} unidades")

    return df_feat, conclusions
