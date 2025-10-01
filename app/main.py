import logging
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from utils.get_data import Data
from utils.data_parser import DataParser
from utils.database import Database, TableCreator
from utils.order_inserter import OrderInserter
from utils.sku_nicho_inserter import SkuNichoInserter
from utils.ml_utils import predict_sales_for_df
import os
import pandas as pd
from datetime import datetime, timedelta

# ------------------------------
# CONFIGURAÇÃO DE LOG
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "database.db")
logger.info(f"Database path set to {db_path}")

# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando lifespan do FastAPI")
    database = Database(db_path)
    database.connect()
    logger.info("Database conectada")
    app.state.database = database

    # Criação de tabelas
    table_creator = TableCreator(database)
    table_creator.create_orders_table()
    table_creator.create_sku_nichos_table()
    logger.info("Tabelas verificadas/criadas")

    # Inserters
    app.state.order_inserter = OrderInserter(database)
    app.state.sku_nicho_inserter = SkuNichoInserter(database)
    logger.info("Inserters inicializados")

    yield
    database.close()
    logger.info("Database desconectada e lifespan finalizado")


app = FastAPI(lifespan=lifespan)

# ------------------------------
# ROTA: Atualiza pedidos da API
@app.post("/update_orders")
def update_orders(date: str = Query(None, description="Data única DD/MM/YYYY ou intervalo DD/MM/YYYY/DD/MM/YYYY")):
    logger.info(f"Chamada para /update_orders com date={date}")
    try:
        if not date:
            date_start = date_end = datetime.today().strftime("%Y-%m-%d")
        else:
            parts = date.split("/")
            if len(parts) == 3:
                day, month, year = parts
                date_start = date_end = f"{year}-{month}-{day}"
            elif len(parts) == 6:
                day1, month1, year1, day2, month2, year2 = parts
                date_start = f"{year1}-{month1}-{day1}"
                date_end = f"{year2}-{month2}-{day2}"
            else:
                logger.warning("Formato de data inválido")
                return {"error": "Formato de data inválido. Use DD/MM/YYYY ou DD/MM/YYYY/DD/MM/YYYY."}

        url = f'https://app.arpcommerce.com.br/sells?r={date_start}' if date_start == date_end else f'https://app.arpcommerce.com.br/sells?r={date_start}/{date_end}'
        logger.info(f"URL gerada para API externa: {url}")

        data = Data(url, {'session': '.eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aMxLsg.3D5e5s_a96H1mPB_uHM7CySJ7n8'})
        raw_json = data.get_data()
        logger.info(f"Dados brutos obtidos: {len(raw_json)} registros")

        parser = DataParser(raw_json)
        orders = parser.parse_orders()
        logger.info(f"Pedidos parseados: {len(orders)} pedidos")

        app.state.order_inserter.insert_orders(orders)
        logger.info(f"{len(orders)} pedidos inseridos no DB com sucesso")
        return {"message": f"{len(orders)} orders updated successfully.", "date_start": date_start, "date_end": date_end}

    except Exception as e:
        logger.exception("Erro ao atualizar pedidos")
        return JSONResponse(status_code=500, content={"error": str(e)})


# RELATÓRIO FLEX (ML + KPIs + Rankings)
@app.get("/report_flex")
def report_flex(start_date: str, end_date: str):
    logger.info(f"Chamada para /report_flex com start_date={start_date}, end_date={end_date}")
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        logger.warning("Datas inválidas fornecidas")
        return JSONResponse(status_code=400, content={"error": "Datas inválidas, use formato YYYY-MM-DD"})

    try:
        db = app.state.database
        cursor = db.conn.cursor()

        def divide_period(start: datetime, end: datetime):
            total_days = (end - start).days + 1
            periods = []
            if total_days <= 7:
                for i in range(total_days):
                    d = start + timedelta(days=i)
                    periods.append((d, d))
            elif total_days <= 28:
                current_start = start
                while current_start <= end:
                    current_end = min(current_start + timedelta(days=6), end)
                    periods.append((current_start, current_end))
                    current_start = current_end + timedelta(days=1)
            else:
                divisor = 7
                while total_days % divisor != 0 and divisor <= total_days:
                    divisor += 1
                block_size = total_days // divisor
                current_start = start
                for _ in range(divisor):
                    current_end = min(current_start + timedelta(days=block_size - 1), end)
                    periods.append((current_start, current_end))
                    current_start = current_end + timedelta(days=1)
            logger.info(f"Períodos divididos: {periods}")
            return periods

        period_blocks = divide_period(start, end)
        reports = []

        def clean_df_for_json(df: pd.DataFrame) -> pd.DataFrame:
            """Substitui NaN por 0 e converte tipos para JSON compatível"""
            return df.fillna(0).replace({pd.NA: 0}).astype(object)

        for b_start, b_end in period_blocks:
            logger.info(f"Processando período {b_start} a {b_end}")
            query = """ SELECT o.*, n.nicho FROM orders o LEFT JOIN sku_nichos n ON o.sku = n.sku
                        WHERE date(o.payment_date) BETWEEN ? AND ? """
            rows = cursor.execute(query, (b_start.strftime("%Y-%m-%d"), b_end.strftime("%Y-%m-%d"))).fetchall()
            cols = [desc[0] for desc in cursor.description]
            logger.info(f"{len(rows)} pedidos encontrados neste período")

            if not rows:
                reports.append({
                    "periodo": {"inicio": b_start.strftime("%Y-%m-%d"), "fim": b_end.strftime("%Y-%m-%d")},
                    "message": "Nenhum pedido encontrado"
                })
                continue

            df = pd.DataFrame(rows, columns=cols)
            df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
            df["day"] = df["payment_date"].dt.date
            df["hour"] = df["payment_date"].dt.hour
            df["weekday"] = df["payment_date"].dt.day_name()
            dias_totais = (b_end - b_start).days + 1

            # Limpa NaNs antes de cálculos
            df_numeric = df.select_dtypes(include='number').fillna(0)
            df.update(df_numeric)

            logger.info("Calculando KPIs gerais")
            kpis = {
                "total_pedidos": len(df),
                "total_unidades": int(df["quantity"].sum()),
                "faturamento_total": float(df["total_value"].sum()),
                "lucro_bruto_total": float(df["gross_profit"].sum()),
                "custo_total": float(df["cost"].sum()),
                "frete_total": float(df["freight"].sum()),
                "impostos_total": float(df["taxes"].sum()),
                "rentabilidade_media": float(df["rentability"].mean() if not df["rentability"].isna().all() else 0),
                "profitabilidade_media": float(df["profitability"].mean() if not df["profitability"].isna().all() else 0),
                "ticket_medio_pedido": float(df["total_value"].sum() / len(df)) if len(df) > 0 else 0,
                "ticket_medio_unidade": float(df["total_value"].sum() / df["quantity"].sum()) if df["quantity"].sum() > 0 else 0
            }

            logger.info("Agrupando por nicho")
            por_nicho = (df.groupby("nicho")
                         .agg({"order_id": "count", "quantity": "sum", "total_value": "sum",
                               "gross_profit": "sum", "freight": "sum", "taxes": "sum", "cost": "sum",
                               "rentability": "mean", "profitability": "mean"})
                         .reset_index()
                         .rename(columns={"order_id": "total_pedidos",
                                          "quantity": "total_unidades",
                                          "total_value": "faturamento_total",
                                          "gross_profit": "lucro_bruto_total"}))
            por_nicho["media_dia_valor"] = por_nicho["faturamento_total"] / dias_totais
            por_nicho["media_dia_unidades"] = por_nicho["total_unidades"] / dias_totais
            por_nicho["participacao_faturamento"] = por_nicho["faturamento_total"] / kpis["faturamento_total"]

            por_nicho = clean_df_for_json(por_nicho)

            # Previsão ML
            df_forecast, conclusions = predict_sales_for_df(df)
            df_forecast = clean_df_for_json(df_forecast)

            reports.append({
                "periodo": {"inicio": b_start.strftime("%Y-%m-%d"), "fim": b_end.strftime("%Y-%m-%d")},
                "kpis_gerais": kpis,
                "analise_nicho": por_nicho.to_dict(orient="records"),
                "forecast_conclusions": conclusions,
                "forecast_data": df_forecast.to_dict(orient="records"),
                "pedidos_brutos": clean_df_for_json(df).to_dict(orient="records")
            })

        logger.info(f"Relatório gerado com {len(reports)} blocos")
        return {"reports": reports}

    except Exception as e:
        logger.exception("Erro ao gerar relatório flex")
        return JSONResponse(status_code=500, content={"error": str(e)})
    logger.info(f"Chamada para /report_flex com start_date={start_date}, end_date={end_date}")
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        logger.warning("Datas inválidas fornecidas")
        return JSONResponse(status_code=400, content={"error": "Datas inválidas, use formato YYYY-MM-DD"})

    try:
        db = app.state.database
        cursor = db.conn.cursor()

        def divide_period(start: datetime, end: datetime):
            total_days = (end - start).days + 1
            periods = []
            if total_days <= 7:
                for i in range(total_days):
                    d = start + timedelta(days=i)
                    periods.append((d, d))
            elif total_days <= 28:
                current_start = start
                while current_start <= end:
                    current_end = min(current_start + timedelta(days=6), end)
                    periods.append((current_start, current_end))
                    current_start = current_end + timedelta(days=1)
            else:
                divisor = 7
                while total_days % divisor != 0 and divisor <= total_days:
                    divisor += 1
                block_size = total_days // divisor
                current_start = start
                for _ in range(divisor):
                    current_end = min(current_start + timedelta(days=block_size - 1), end)
                    periods.append((current_start, current_end))
                    current_start = current_end + timedelta(days=1)
            logger.info(f"Períodos divididos: {periods}")
            return periods

        period_blocks = divide_period(start, end)
        reports = []

        for b_start, b_end in period_blocks:
            logger.info(f"Processando período {b_start} a {b_end}")
            query = """ SELECT o.*, n.nicho FROM orders o LEFT JOIN sku_nichos n ON o.sku = n.sku
                        WHERE date(o.payment_date) BETWEEN ? AND ? """
            rows = cursor.execute(query, (b_start.strftime("%Y-%m-%d"), b_end.strftime("%Y-%m-%d"))).fetchall()
            cols = [desc[0] for desc in cursor.description]
            logger.info(f"{len(rows)} pedidos encontrados neste período")

            if not rows:
                reports.append({
                    "periodo": {"inicio": b_start.strftime("%Y-%m-%d"), "fim": b_end.strftime("%Y-%m-%d")},
                    "message": "Nenhum pedido encontrado"
                })
                continue

            df = pd.DataFrame(rows, columns=cols)
            df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
            df["day"] = df["payment_date"].dt.date
            df["hour"] = df["payment_date"].dt.hour
            df["weekday"] = df["payment_date"].dt.day_name()
            dias_totais = (b_end - b_start).days + 1

            logger.info("Calculando KPIs gerais")
            kpis = {
                "total_pedidos": len(df),
                "total_unidades": int(df["quantity"].sum()),
                "faturamento_total": float(df["total_value"].sum()),
                "lucro_bruto_total": float(df["gross_profit"].sum()),
                "custo_total": float(df["cost"].sum()),
                "frete_total": float(df["freight"].sum()),
                "impostos_total": float(df["taxes"].sum()),
                "rentabilidade_media": float(df["rentability"].mean() if not df["rentability"].isna().all() else 0),
                "profitabilidade_media": float(df["profitability"].mean() if not df["profitability"].isna().all() else 0),
                "ticket_medio_pedido": float(df["total_value"].sum() / len(df)),
                "ticket_medio_unidade": float(df["total_value"].sum() / df["quantity"].sum())
            }

            logger.info("Agrupando por nicho")
            por_nicho = (df.groupby("nicho")
                         .agg({"order_id": "count", "quantity": "sum", "total_value": "sum",
                               "gross_profit": "sum", "freight": "sum", "taxes": "sum", "cost": "sum",
                               "rentability": "mean", "profitability": "mean"})
                         .reset_index()
                         .rename(columns={"order_id": "total_pedidos",
                                          "quantity": "total_unidades",
                                          "total_value": "faturamento_total",
                                          "gross_profit": "lucro_bruto_total"}))
            por_nicho["media_dia_valor"] = por_nicho["faturamento_total"] / dias_totais
            por_nicho["media_dia_unidades"] = por_nicho["total_unidades"] / dias_totais
            por_nicho["participacao_faturamento"] = por_nicho["faturamento_total"] / kpis["faturamento_total"]

            # Previsão ML
            df_forecast, conclusions = predict_sales_for_df(df)
            logger.info(f"Forecast gerado com {len(df_forecast)} registros")

            reports.append({
                "periodo": {"inicio": b_start.strftime("%Y-%m-%d"), "fim": b_end.strftime("%Y-%m-%d")},
                "kpis_gerais": kpis,
                "analise_nicho": por_nicho.to_dict(orient="records"),
                "forecast_conclusions": conclusions,
                "forecast_data": df_forecast.to_dict(orient="records"),
                "pedidos_brutos": df.to_dict(orient="records")
            })

        logger.info(f"Relatório gerado com {len(reports)} blocos")
        return {"reports": reports}

    except Exception as e:
        logger.exception("Erro ao gerar relatório flex")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ------------------------------
# CRUD de SKU/NICHOS com logs
@app.post("/sku_nicho/insert_one")
def insert_sku_nicho(sku: str, nicho: str):
    logger.info(f"Inserindo SKU {sku} no nicho {nicho}")
    app.state.sku_nicho_inserter.insert_one(sku, nicho)
    logger.info(f"SKU {sku} inserido com sucesso")
    return {"message": f"SKU {sku} inserido no nicho {nicho} com sucesso."}

@app.post("/sku_nicho/insert_many")
def insert_many_sku_nicho(sku_nicho_list: list[dict]):
    logger.info(f"Inserindo {len(sku_nicho_list)} registros de SKU/nicho")
    for item in sku_nicho_list:
        if "sku" not in item or "nicho" not in item:
            logger.warning(f"Registro inválido: {item}")
            return JSONResponse(status_code=400, content={"error": "Cada item deve conter 'sku' e 'nicho'"})
    app.state.sku_nicho_inserter.insert_many(sku_nicho_list)
    logger.info("Inserção múltipla concluída")
    return {"message": f"{len(sku_nicho_list)} registros inseridos com sucesso."}

@app.put("/sku_nicho/update")
def update_sku_nicho(sku: str, new_nicho: str):
    logger.info(f"Atualizando SKU {sku} para nicho {new_nicho}")
    updated_count = app.state.sku_nicho_inserter.update_nicho(sku, new_nicho)
    logger.info(f"{updated_count} registros atualizados")
    return {"message": f"{updated_count} registro(s) atualizado(s)."}

@app.delete("/sku_nicho/delete")
def delete_sku_nicho(sku: str):
    logger.info(f"Deletando SKU {sku}")
    deleted_count = app.state.sku_nicho_inserter.delete_sku(sku)
    logger.info(f"{deleted_count} registros deletados")
    return {"message": f"{deleted_count} registro(s) apagado(s)."}

@app.get("/sku_nicho/list")
def list_sku_nicho():
    logger.info("Listando todos os SKU/nichos")
    rows = app.state.sku_nicho_inserter.list_all()
    logger.info(f"{len(rows)} registros retornados")
    return {"data": rows}
