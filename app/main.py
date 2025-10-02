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
logger.info(f"Caminho do banco de dados definido em {db_path}")

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
@app.post("/atualizar_pedidos")
def atualizar_pedidos(data: str = Query(None, description="Data única DD/MM/YYYY ou intervalo DD/MM/YYYY/DD/MM/YYYY")):
    logger.info(f"Chamada para /atualizar_pedidos com data={data}")
    try:
        if not data:
            data_inicio = data_fim = datetime.today().strftime("%Y-%m-%d")
        else:
            partes = data.split("/")
            if len(partes) == 3:
                dia, mes, ano = partes
                data_inicio = data_fim = f"{ano}-{mes}-{dia}"
            elif len(partes) == 6:
                dia1, mes1, ano1, dia2, mes2, ano2 = partes
                data_inicio = f"{ano1}-{mes1}-{dia1}"
                data_fim = f"{ano2}-{mes2}-{dia2}"
            else:
                logger.warning("Formato de data inválido")
                return {"erro": "Formato de data inválido. Use DD/MM/YYYY ou DD/MM/YYYY/DD/MM/YYYY."}

        url = f'https://app.arpcommerce.com.br/sells?r={data_inicio}' if data_inicio == data_fim else f'https://app.arpcommerce.com.br/sells?r={data_inicio}/{data_fim}'
        logger.info(f"URL gerada para API externa: {url}")

        data_obj = Data(url, {'session': '.eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aMxLsg.3D5e5s_a96H1mPB_uHM7CySJ7n8'})
        raw_json = data_obj.get_data()
        logger.info(f"Dados brutos obtidos: {len(raw_json)} registros")

        parser = DataParser(raw_json)
        pedidos = parser.parse_orders()
        logger.info(f"Pedidos parseados: {len(pedidos)} pedidos")

        app.state.order_inserter.insert_orders(pedidos)
        logger.info(f"{len(pedidos)} pedidos inseridos no DB com sucesso")
        return {"mensagem": f"{len(pedidos)} pedidos atualizados com sucesso.", "data_inicio": data_inicio, "data_fim": data_fim}

    except Exception as e:
        logger.exception("Erro ao atualizar pedidos")
        return JSONResponse(status_code=500, content={"erro": str(e)})


# ------------------------------
# RELATÓRIO FLEX (ML + KPIs + Rankings)
# ------------------------------
# ------------------------------
# RELATÓRIO FLEX (ML + KPIs + Rankings)
@app.get("/relatorio_flex")
def relatorio_flex(data_inicio: str = None, data_fim: str = None):
    logger.info(f"Chamada para /relatorio_flex com data_inicio={data_inicio}, data_fim={data_fim}")
    try:
        if not data_inicio or not data_fim:
            hoje = datetime.today().strftime("%Y-%m-%d")
            data_inicio = data_fim = hoje

        start = datetime.strptime(data_inicio, "%Y-%m-%d")
        end = datetime.strptime(data_fim, "%Y-%m-%d")
    except Exception:
        logger.warning("Datas inválidas fornecidas")
        return JSONResponse(status_code=400, content={"erro": "Datas inválidas, use formato YYYY-MM-DD"})

    try:
        db = app.state.database
        cursor = db.conn.cursor()

        # 1) Obter todos os dados do período completo
        query = """ SELECT o.*, n.nicho FROM orders o LEFT JOIN sku_nichos n ON o.sku = n.sku
                    WHERE date(o.payment_date) BETWEEN ? AND ? """
        linhas = cursor.execute(query, (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))).fetchall()
        colunas = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(linhas, columns=colunas)
        if df.empty:
            return {"mensagem": "Nenhum pedido encontrado neste período", "skus_sem_nicho": []}

        df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
        dias_totais = (end - start).days + 1

        # Função de limpeza para JSON
        def limpar_df_para_json(df: pd.DataFrame) -> pd.DataFrame:
            return df.fillna(0).replace({pd.NA: 0}).astype(object)

        # 2) KPIs gerais
        skus_sem_nicho = df[df["nicho"].isna()]["sku"].unique().tolist()
        lucro_liquido_total = df["profit"].sum()
        kpis_gerais = {
            "lucro_liquido_total": float(lucro_liquido_total),
            "lucro_bruto_total": float(df["gross_profit"].sum()),
            "total_pedidos": len(df),
            "total_unidades": int(df["quantity"].sum()),
            "faturamento_total": float(df["total_value"].sum()),
            "custo_total": float(df["cost"].sum()),
            "frete_total": float(df["freight"].sum()),
            "impostos_total": float(df["taxes"].sum()),
            "rentabilidade_media": float(df["rentability"].mean() if not df["rentability"].isna().all() else 0),
            "profitabilidade_media": float(df["profitability"].mean() if not df["profitability"].isna().all() else 0),
            "ticket_medio_pedido": float(df["total_value"].sum() / len(df)) if len(df) > 0 else 0,
            "ticket_medio_unidade": float(df["total_value"].sum() / df["quantity"].sum()) if df["quantity"].sum() > 0 else 0,
            "skus_sem_nicho": skus_sem_nicho
        }

        # 3) Relatórios diários detalhados
        relatorios_diarios = []
        relatorios_diarios_por_nicho = []

        for dia, grupo_dia in df.groupby(df["payment_date"].dt.date):
            total_pedidos = len(grupo_dia)
            total_unidades = int(grupo_dia["quantity"].sum())
            faturamento = float(grupo_dia["total_value"].sum())
            lucro_liquido = float(grupo_dia["profit"].sum())
            lucro_bruto = float(grupo_dia["gross_profit"].sum())
            custo = float(grupo_dia["cost"].sum())
            frete = float(grupo_dia["freight"].sum())
            impostos = float(grupo_dia["taxes"].sum())
            rentabilidade_media = float(grupo_dia["rentability"].mean() if not grupo_dia["rentability"].isna().all() else 0)
            profitabilidade_media = float(grupo_dia["profitability"].mean() if not grupo_dia["profitability"].isna().all() else 0)
            ticket_medio_pedido = faturamento / total_pedidos if total_pedidos > 0 else 0
            ticket_medio_unidade = faturamento / total_unidades if total_unidades > 0 else 0
            skus_sem_nicho_dia = grupo_dia[grupo_dia["nicho"].isna()]["sku"].unique().tolist()

            relatorios_diarios.append({
                "dia": dia.strftime("%Y-%m-%d") if isinstance(dia, datetime) else str(dia),
                "lucro_liquido": lucro_liquido,
                "lucro_bruto": lucro_bruto,
                "total_pedidos": total_pedidos,
                "total_unidades": total_unidades,
                "faturamento": faturamento,
                "custo": custo,
                "frete": frete,
                "impostos": impostos,
                "rentabilidade_media": rentabilidade_media,
                "profitabilidade_media": profitabilidade_media,
                "ticket_medio_pedido": ticket_medio_pedido,
                "ticket_medio_unidade": ticket_medio_unidade,
                "skus_sem_nicho": skus_sem_nicho_dia
            })

            # Relatório diário por nicho
            for nicho, grupo_nicho in grupo_dia.groupby("nicho"):
                total_pedidos_nicho = len(grupo_nicho)
                total_unidades_nicho = int(grupo_nicho["quantity"].sum())
                faturamento_nicho = float(grupo_nicho["total_value"].sum())
                lucro_liquido_nicho = float(grupo_nicho["profit"].sum())
                lucro_bruto_nicho = float(grupo_nicho["gross_profit"].sum())

                relatorios_diarios_por_nicho.append({
                    "dia": dia.strftime("%Y-%m-%d") if isinstance(dia, datetime) else str(dia),
                    "nicho": nicho if nicho else "Sem nicho",
                    "lucro_liquido": lucro_liquido_nicho,
                    "lucro_bruto": lucro_bruto_nicho,
                    "total_pedidos": total_pedidos_nicho,
                    "total_unidades": total_unidades_nicho,
                    "faturamento": faturamento_nicho
                })

        # 4) Análise por nicho geral (lucro na frente)
        por_nicho = (df.groupby("nicho")
                     .agg({"profit": "sum", "gross_profit": "sum", "order_id": "count", "quantity": "sum",
                           "total_value": "sum", "freight": "sum", "taxes": "sum", "cost": "sum",
                           "rentability": "mean", "profitability": "mean"})
                     .reset_index()
                     .rename(columns={"profit": "lucro_liquido",
                                      "gross_profit": "lucro_bruto",
                                      "order_id": "total_pedidos",
                                      "quantity": "total_unidades",
                                      "total_value": "faturamento_total"}))
        por_nicho["participacao_faturamento"] = por_nicho["faturamento_total"] / kpis_gerais["faturamento_total"] if kpis_gerais["faturamento_total"] != 0 else 0
        por_nicho["participacao_lucro"] = por_nicho["lucro_liquido"] / kpis_gerais["lucro_liquido_total"] if kpis_gerais["lucro_liquido_total"] != 0 else 0
        por_nicho["media_dia_valor"] = por_nicho["faturamento_total"] / dias_totais
        por_nicho["media_dia_unidades"] = por_nicho["total_unidades"] / dias_totais
        por_nicho = limpar_df_para_json(por_nicho)

        # 5) Forecast ML
        df_forecast, conclusoes = predict_sales_for_df(df)
        df_forecast = limpar_df_para_json(df_forecast)

        # 6) Rankings detalhados com lucro na frente
        top_30_ads = (df.groupby("ad")
                         .agg({"profit": "sum", "gross_profit": "sum"})
                         .sort_values("profit", ascending=False)
                         .head(30)
                         .reset_index())
        top_30_ads = limpar_df_para_json(top_30_ads)

        top_30_skus = (df.groupby("sku")
                          .agg({"profit": "sum", "gross_profit": "sum"})
                          .sort_values("profit", ascending=False)
                          .head(30)
                          .reset_index())
        top_30_skus = limpar_df_para_json(top_30_skus)

        top_15_por_nicho = (df.groupby(["nicho", "sku"])
                               .agg({"profit": "sum", "gross_profit": "sum"})
                               .sort_values(["nicho", "profit"], ascending=[True, False])
                               .groupby(level=0).head(15).reset_index())
        top_15_por_nicho = limpar_df_para_json(top_15_por_nicho)

        logger.info("Relatório flex gerado com sucesso")
        return {
            "periodo": {"inicio": start.strftime("%Y-%m-%d"), "fim": end.strftime("%Y-%m-%d")},
            "kpis_gerais": kpis_gerais,
            "relatorios_diarios": relatorios_diarios,
            "relatorios_diarios_por_nicho": relatorios_diarios_por_nicho,
            "analise_por_nicho": por_nicho.to_dict(orient="records"),
            "conclusoes_forecast": conclusoes,
            "forecast": df_forecast.to_dict(orient="records"),
            "top_30_ads": top_30_ads.to_dict(orient="records"),
            "top_30_skus": top_30_skus.to_dict(orient="records"),
            "top_15_por_nicho": top_15_por_nicho.to_dict(orient="records")
        }

    except Exception as e:
        logger.exception("Erro ao gerar relatório flex")
        return JSONResponse(status_code=500, content={"erro": str(e)})

# ------------------------------
# CRUD de SKU/NICHOS com logs
@app.post("/sku_nicho/inserir")
def inserir_sku_nicho(sku: str, nicho: str):
    logger.info(f"Inserindo SKU {sku} no nicho {nicho}")
    app.state.sku_nicho_inserter.insert_one(sku, nicho)
    logger.info(f"SKU {sku} inserido com sucesso")
    return {"mensagem": f"SKU {sku} inserido no nicho {nicho} com sucesso."}

@app.post("/sku_nicho/inserir_varios")
def inserir_varios_sku_nicho(sku_nicho_lista: list[dict]):
    logger.info(f"Inserindo {len(sku_nicho_lista)} registros de SKU/nicho")
    for item in sku_nicho_lista:
        if "sku" not in item or "nicho" not in item:
            logger.warning(f"Registro inválido: {item}")
            return JSONResponse(status_code=400, content={"erro": "Cada item deve conter 'sku' e 'nicho'"})
    app.state.sku_nicho_inserter.insert_many(sku_nicho_lista)
    logger.info("Inserção múltipla concluída")
    return {"mensagem": f"{len(sku_nicho_lista)} registros inseridos com sucesso."}

@app.put("/sku_nicho/atualizar")
def atualizar_sku_nicho(sku: str, novo_nicho: str):
    logger.info(f"Atualizando SKU {sku} para nicho {novo_nicho}")
    atualizados = app.state.sku_nicho_inserter.update_nicho(sku, novo_nicho)
    logger.info(f"{atualizados} registros atualizados")
    return {"mensagem": f"{atualizados} registro(s) atualizado(s)."}

@app.delete("/sku_nicho/deletar")
def deletar_sku_nicho(sku: str):
    logger.info(f"Deletando SKU {sku}")
    deletados = app.state.sku_nicho_inserter.delete_sku(sku)
    logger.info(f"{deletados} registros deletados")
    return {"mensagem": f"{deletados} registro(s) apagado(s)."}

@app.get("/sku_nicho/listar")
def listar_sku_nicho():
    logger.info("Listando todos os SKU/nichos")
    rows = app.state.sku_nicho_inserter.list_all()
    logger.info(f"{len(rows)} registros retornados")
    return {"dados": rows}

# ------------------------------
# ROTA: Listar todos os pedidos
@app.get("/orders")
def listar_orders():
    logger.info("Listando todos os pedidos da tabela orders")
    try:
        db = app.state.database
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM orders")
        linhas = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(linhas, columns=colunas)
        df = df.fillna(0).replace({pd.NA: 0}).astype(object)  # Limpeza básica

        logger.info(f"{len(df)} pedidos encontrados")
        return {"total_pedidos": len(df), "pedidos": df.to_dict(orient="records")}
    except Exception as e:
        logger.exception("Erro ao listar pedidos")
        return JSONResponse(status_code=500, content={"erro": str(e)})
# ------------------------------
# ROTA: Listar pedidos por período
@app.get("/orders/periodo")
def listar_orders_periodo(data_inicio: str, data_fim: str):
    logger.info(f"Listando pedidos entre {data_inicio} e {data_fim}")
    try:
        # Validar formato
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            fim = datetime.strptime(data_fim, "%Y-%m-%d")
        except ValueError:
            logger.warning("Datas inválidas fornecidas")
            return JSONResponse(status_code=400, content={"erro": "Datas inválidas, use formato YYYY-MM-DD"})

        db = app.state.database
        cursor = db.conn.cursor()
        query = """
            SELECT * FROM orders
            WHERE date(payment_date) BETWEEN ? AND ?
        """
        cursor.execute(query, (data_inicio, data_fim))
        linhas = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(linhas, columns=colunas)
        df = df.fillna(0).replace({pd.NA: 0}).astype(object)  # Limpeza básica

        logger.info(f"{len(df)} pedidos encontrados no período")
        return {
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "total_pedidos": len(df),
            "pedidos": df.to_dict(orient="records")
        }
    except Exception as e:
        logger.exception("Erro ao listar pedidos por período")
        return JSONResponse(status_code=500, content={"erro": str(e)})