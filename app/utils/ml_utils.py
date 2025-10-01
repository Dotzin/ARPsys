import pandas as pd
from joblib import dump, load
import lightgbm as lgb
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

MODEL_PATH = "models/profit_forecast_model.pkl"

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Extraindo features do dataframe")
    df = df.copy()
    df["payment_date"] = pd.to_datetime(df["payment_date"])
    df["hour"] = df["payment_date"].dt.hour
    df["weekday"] = df["payment_date"].dt.weekday
    df["month"] = df["payment_date"].dt.month

    # Usa a coluna profit do DB
    df["lucro_liquido"] = df["profit"]

    logger.info("Calculando médias por SKU, nicho e loja com lucro_liquido")
    df["sku_avg_profit"] = df.groupby("sku")["lucro_liquido"].transform("mean")
    df["nicho_avg_profit"] = df.groupby("nicho")["lucro_liquido"].transform("mean")
    df["store_avg_profit"] = df.groupby("store")["lucro_liquido"].transform("mean")

    # Outras features opcionais
    df["total_value_per_unit"] = df["total_value"] / df["quantity"].replace(0, 1)
    df["profit_per_unit"] = df["lucro_liquido"] / df["quantity"].replace(0, 1)

    return df

def train_ml_model(df: pd.DataFrame):
    logger.info("Iniciando treinamento do modelo ML de lucro_liquido")
    df_feat = extract_features(df)
    df_feat = df_feat.sort_values(["sku", "payment_date"])

    # Criação do alvo: lucro_liquido do próximo dia
    df_feat["target_profit_next_day"] = df_feat.groupby("sku")["lucro_liquido"].shift(-1)
    df_train = df_feat.dropna(subset=["target_profit_next_day"])
    logger.info(f"{len(df_train)} registros disponíveis para treinamento")

    features = [
        "lucro_liquido", "total_value", "quantity", "cost", "freight", "taxes",
        "sku_avg_profit", "nicho_avg_profit", "store_avg_profit",
        "weekday", "hour", "month"
    ]
    X = df_train[features]
    y = df_train["target_profit_next_day"]

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
    logger.info("Iniciando previsão de lucro_liquido")
    if not Path(MODEL_PATH).exists():
        logger.error("Modelo ML não encontrado. Execute train_ml_model() primeiro.")
        raise FileNotFoundError("Modelo ML não encontrado. Execute train_ml_model() primeiro.")

    model = load(MODEL_PATH)
    logger.info("Modelo ML carregado com sucesso")

    df_feat = extract_features(df)
    features = [
        "lucro_liquido", "total_value", "quantity", "cost", "freight", "taxes",
        "sku_avg_profit", "nicho_avg_profit", "store_avg_profit",
        "weekday", "hour", "month"
    ]
    X = df_feat[features]
    df_feat["forecast_profit_next_day"] = model.predict(X)
    logger.info("Previsão concluída para todos os registros")

    conclusions = []

    # Nicho
    top_nichos = df_feat.groupby("nicho")["forecast_profit_next_day"].sum().sort_values(ascending=False)
    if not top_nichos.empty:
        conclusions.append({
            "melhor_nicho_previsto": top_nichos.idxmax(),
            "lucro_previsto": float(top_nichos.max())
        })
        logger.info(f"Melhor nicho previsto: {top_nichos.idxmax()} com lucro {top_nichos.max()}")

    # Produto
    top_produtos = df_feat.groupby("sku")["forecast_profit_next_day"].sum().sort_values(ascending=False)
    if not top_produtos.empty:
        conclusions.append({
            "melhor_produto_previsto": top_produtos.idxmax(),
            "lucro_previsto": float(top_produtos.max())
        })
        logger.info(f"Melhor produto previsto: {top_produtos.idxmax()} com lucro {top_produtos.max()}")

    # Hora pico
    peak_hours = df_feat.groupby("hour")["forecast_profit_next_day"].sum().sort_values(ascending=False)
    if not peak_hours.empty:
        conclusions.append({
            "hora_pico_prevista": int(peak_hours.idxmax()),
            "lucro_previsto": float(peak_hours.max())
        })
        logger.info(f"Hora pico prevista: {int(peak_hours.idxmax())} com lucro {peak_hours.max()}")

    return df_feat, conclusions
