import pandas as pd
from joblib import dump, load
import lightgbm as lgb
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "profit_forecast_model.pkl"
MODEL_PATH_STR = str(MODEL_PATH)
logger.info(f"Caminho absoluto do modelo definido como: {MODEL_PATH_STR}")

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Extraindo features do dataframe")
    df = df.copy()
    df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
    df["hour"] = df["payment_date"].dt.hour
    df["weekday"] = df["payment_date"].dt.weekday
    df["month"] = df["payment_date"].dt.month
    df["lucro_liquido"] = df["gross_profit"] - df["taxes"] - df["freight"] - df["cost"]
    df["sku_avg_profit"] = df.groupby("sku")["lucro_liquido"].transform("mean")
    df["nicho_avg_profit"] = df.groupby("nicho")["lucro_liquido"].transform("mean")
    df["store_avg_profit"] = df.groupby("store")["lucro_liquido"].transform("mean")
    df["total_value_per_unit"] = df["total_value"] / df["quantity"].replace(0, 1)
    df["profit_per_unit"] = df["lucro_liquido"] / df["quantity"].replace(0, 1)
    return df

def train_ml_model(df: pd.DataFrame):
    logger.info("Iniciando treinamento do modelo ML de lucro_liquido")
    df_feat = extract_features(df)
    df_feat = df_feat.sort_values(["sku", "payment_date"])
    df_feat["target_lucro_liquido_next"] = df_feat.groupby("sku")["lucro_liquido"].shift(-1)
    df_train = df_feat.dropna(subset=["target_lucro_liquido_next"])
    logger.info(f"{len(df_train)} registros disponíveis para treinar com target futuro")
    if df_train.empty:
        logger.warning("Nenhum SKU tem mais de um pedido. Treinamento não será possível.")
        return None
    features = [
        "lucro_liquido", "total_value", "quantity", "cost", "freight", "taxes",
        "sku_avg_profit", "nicho_avg_profit", "store_avg_profit",
        "weekday", "hour", "month"
    ]
    X = df_train[features]
    y = df_train["target_lucro_liquido_next"]
    model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05, num_leaves=31)
    model.fit(X, y)
    logger.info("Modelo treinado com sucesso")
    model_dir = Path(MODEL_PATH_STR).parent
    if not model_dir.exists():
        os.makedirs(model_dir)
        logger.info(f"Pasta '{model_dir}' criada")
    dump(model, MODEL_PATH_STR)
    logger.info(f"Modelo salvo em {MODEL_PATH_STR}")
    return model

def predict_sales_for_df(df: pd.DataFrame):
    logger.info("Iniciando previsão de lucro_liquido")
    if not Path(MODEL_PATH_STR).exists():
        logger.error(f"Modelo ML não encontrado em {MODEL_PATH_STR}. Execute train_ml_model() primeiro.")
        raise FileNotFoundError(f"Modelo ML não encontrado. Execute train_ml_model() primeiro. Esperado em: {MODEL_PATH_STR}")
    model = load(MODEL_PATH_STR)
    logger.info("Modelo ML carregado com sucesso")
    df_feat = extract_features(df)
    df_feat = df_feat.dropna(subset=["sku"])
    df_feat = df_feat.fillna(0)
    features = [
        "lucro_liquido", "total_value", "quantity", "cost", "freight", "taxes",
        "sku_avg_profit", "nicho_avg_profit", "store_avg_profit",
        "weekday", "hour", "month"
    ]

    # Previsões para dados históricos (para conclusões)
    X = df_feat[features]
    df_feat["forecast_lucro_liquido_next"] = model.predict(X)
    logger.info("Previsão concluída para todos os registros históricos")

    # Previsões para os próximos 7 dias baseadas na média histórica diária
    from datetime import datetime, timedelta
    today = datetime.today().date()
    # Calcular médias diárias históricas
    daily_avg = df_feat.groupby(df_feat["payment_date"].dt.date).agg({
        "lucro_liquido": "sum",
        "quantity": "sum",
        "total_value": "sum"
    }).mean()

    future_predictions = []
    for days_ahead in range(1, 8):
        future_date = today + timedelta(days=days_ahead)
        future_predictions.append({
            "payment_date": future_date,
            "forecast_lucro_liquido_next": daily_avg["lucro_liquido"],
            "quantity": daily_avg["quantity"],
            "total_value": daily_avg["total_value"]
        })

    if future_predictions:
        df_future = pd.DataFrame(future_predictions)
        logger.info("Previsões futuras geradas para os próximos 7 dias baseadas na média histórica")

    conclusions = []
    top_nichos = df_feat.groupby("nicho")["forecast_lucro_liquido_next"].sum().sort_values(ascending=False)
    if not top_nichos.empty:
        conclusions.append({
            "melhor_nicho_previsto": top_nichos.idxmax(),
            "lucro_previsto": float(top_nichos.max())
        })
    top_produtos = df_feat.groupby("sku")["forecast_lucro_liquido_next"].sum().sort_values(ascending=False)
    if not top_produtos.empty:
        conclusions.append({
            "melhor_produto_previsto": top_produtos.idxmax(),
            "lucro_previsto": float(top_produtos.max())
        })
    peak_hours = df_feat.groupby("hour")["forecast_lucro_liquido_next"].sum().sort_values(ascending=False)
    if not peak_hours.empty:
        conclusions.append({
            "hora_pico_prevista": int(peak_hours.idxmax()),
            "lucro_previsto": float(peak_hours.max())
        })

    # Agregar previsões por data (diário para os próximos 7 dias)
    if future_predictions:
        df_forecast = df_future.groupby("payment_date").agg({
            "forecast_lucro_liquido_next": "sum",
            "quantity": "sum",
            "total_value": "sum"
        }).reset_index().rename(columns={
            "forecast_lucro_liquido_next": "previsao_lucro_diario",
            "quantity": "quantidade_total_diaria",
            "total_value": "valor_total_diario"
        })
        # Arredondar para 2 casas decimais
        df_forecast["previsao_lucro_diario"] = df_forecast["previsao_lucro_diario"].round(2)
        df_forecast["quantidade_total_diaria"] = df_forecast["quantidade_total_diaria"].round(2)
        df_forecast["valor_total_diario"] = df_forecast["valor_total_diario"].round(2)
    else:
        df_forecast = pd.DataFrame()  # Fallback

    return df_forecast, conclusions
