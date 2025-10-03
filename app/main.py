import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from utils.get_data import Data
from utils.data_parser import DataParser
from utils.database import Database, TableCreator
from utils.order_inserter import OrderInserter
from utils.sku_nicho_inserter import SkuNichoInserter
from utils.ml_utils import predict_sales_for_df
import os
import requests
import pandas as pd
from datetime import datetime
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



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
# GERENCIADOR DE WEBSOCKET
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Cliente WebSocket conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Cliente WebSocket desconectado. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Falha ao enviar mensagem WebSocket: {e}")

ws_manager = ConnectionManager()

# ------------------------------
# WATCHER DE DB
class DBChangeHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("database.db"):
            logger.info("Alteração detectada no banco de dados")
            asyncio.run_coroutine_threadsafe(notify_ws_db_change(), self.loop)

async def notify_ws_db_change():
    try:
        relatorio = await gerar_relatorio_diario()
        await ws_manager.broadcast(relatorio)
        logger.info("Relatório diário enviado via WebSocket após alteração no DB")
    except Exception as e:
        logger.exception(f"Erro ao enviar relatório WS após alteração: {e}")

# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando lifespan do FastAPI")
    database = Database(db_path)
    database.connect()
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

    # Scheduler para atualizar pedidos automaticamente
    scheduler = AsyncIOScheduler()
    async def atualizar_pedidos_automatico():
        try:
            logger.info("Iniciando atualização automática de pedidos...")
            url = "https://app.arpcommerce.com.br/sells?r=" + datetime.today().strftime("%Y-%m-%d")
            cookies = {
                "session": ".eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aN66kw.LykMym2ZnpFAMEGup9iIxbDwVpg"
            }
            response = requests.get(url, cookies=cookies)
            response.raise_for_status()
            raw_json = response.json()
            parser = DataParser(raw_json)
            pedidos = parser.parse_orders()
            app.state.order_inserter.insert_orders(pedidos)
            logger.info(f"{len(pedidos)} pedidos inseridos no DB automaticamente")
        except Exception as e:
            logger.exception(f"Erro na atualização automática de pedidos: {e}")

    scheduler.add_job(lambda: asyncio.create_task(atualizar_pedidos_automatico()), 'interval', minutes=5)
    scheduler.start()
    await atualizar_pedidos_automatico()

    # Inicia watcher do DB
    loop = asyncio.get_event_loop()
    event_handler = DBChangeHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path=BASE_DIR, recursive=False)
    observer.start()
    logger.info("Watcher do DB iniciado")

    yield

    scheduler.shutdown()
    observer.stop()
    observer.join()
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

        data_obj = Data(url, {'session': '.eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aN66kw.LykMym2ZnpFAMEGup9iIxbDwVpg'})
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




@app.get("/relatorio_flex")
def relatorio_flex(data_inicio: str = None, data_fim: str = None):
    logger.info(f"Chamada para /relatorio_flex com data_inicio={data_inicio}, data_fim={data_fim}")
    try:
        # ------------------------------
        # Validar datas
        if not data_inicio or not data_fim:
            hoje = datetime.today().strftime("%Y-%m-%d")
            data_inicio = data_fim = hoje

        start = datetime.strptime(data_inicio, "%Y-%m-%d")
        end = datetime.strptime(data_fim, "%Y-%m-%d")
        dias_totais = (end - start).days + 1

        # ------------------------------
        # Obter dados do DB
        db = app.state.database
        cursor = db.conn.cursor()
        query = """ SELECT o.*, n.nicho FROM orders o LEFT JOIN sku_nichos n ON o.sku = n.sku
                    WHERE date(o.payment_date) BETWEEN ? AND ? """
        linhas = cursor.execute(query, (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))).fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(linhas, columns=colunas)

        if df.empty:
            return {"mensagem": "Nenhum pedido encontrado neste período", "skus_sem_nicho": []}

        df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")

        # ------------------------------
        # Calcular lucro líquido
        df["lucro_liquido"] = df["gross_profit"] - df["cost"] - df["freight"] - df["taxes"]
        df["lucro_liquido_por_unidade"] = df["lucro_liquido"] / df["quantity"].replace(0, 1)

        # Função de limpeza
        def limpar_df_para_json(df: pd.DataFrame) -> pd.DataFrame:
            return df.fillna(0).replace({pd.NA: 0}).astype(object)

        # ------------------------------
        # KPIs gerais
        skus_sem_nicho = df[df["nicho"].isna()]["sku"].unique().tolist()
        lucro_liquido_total = df["lucro_liquido"].sum()
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
            "lucro_liquido_medio_por_pedido": float(df["lucro_liquido"].sum() / len(df)) if len(df) > 0 else 0,
            "lucro_liquido_medio_por_unidade": float(df["lucro_liquido"].sum() / df["quantity"].sum()) if df["quantity"].sum() > 0 else 0,
            "skus_sem_nicho": skus_sem_nicho
        }

        # ------------------------------
        # Relatórios diários
        relatorios_diarios = []
        relatorios_diarios_por_nicho = []
        relatorios_diarios_anuncios = []

        for dia, grupo_dia in df.groupby(df["payment_date"].dt.date):
            total_pedidos = len(grupo_dia)
            total_unidades = int(grupo_dia["quantity"].sum())
            faturamento = float(grupo_dia["total_value"].sum())
            lucro_liquido = float(grupo_dia["lucro_liquido"].sum())
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
                "dia": str(dia),
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
                "lucro_liquido_medio_por_pedido": lucro_liquido / total_pedidos if total_pedidos > 0 else 0,
                "lucro_liquido_medio_por_unidade": lucro_liquido / total_unidades if total_unidades > 0 else 0,
                "skus_sem_nicho": skus_sem_nicho_dia
            })

            # Diário por nicho
            for nicho, grupo_nicho in grupo_dia.groupby("nicho"):
                total_pedidos_nicho = len(grupo_nicho)
                total_unidades_nicho = int(grupo_nicho["quantity"].sum())
                faturamento_nicho = float(grupo_nicho["total_value"].sum())
                lucro_liquido_nicho = float(grupo_nicho["lucro_liquido"].sum())
                lucro_bruto_nicho = float(grupo_nicho["gross_profit"].sum())

                relatorios_diarios_por_nicho.append({
                    "dia": str(dia),
                    "nicho": nicho if nicho else "Sem nicho",
                    "lucro_liquido": lucro_liquido_nicho,
                    "lucro_bruto": lucro_bruto_nicho,
                    "total_pedidos": total_pedidos_nicho,
                    "total_unidades": total_unidades_nicho,
                    "faturamento": faturamento_nicho,
                    "lucro_liquido_medio_por_pedido": lucro_liquido_nicho / total_pedidos_nicho if total_pedidos_nicho > 0 else 0,
                    "lucro_liquido_medio_por_unidade": lucro_liquido_nicho / total_unidades_nicho if total_unidades_nicho > 0 else 0
                })

            # Diário por anúncios
            grupo_ads = (grupo_dia.groupby(["ad", "sku"])
                         .agg({"lucro_liquido": "sum", "gross_profit": "sum", "quantity": "sum", "total_value": "sum"})
                         .reset_index())
            relatorios_diarios_anuncios.append({
                "dia": str(dia),
                "anuncios": limpar_df_para_json(grupo_ads).to_dict(orient="records")
            })

        # ------------------------------
        # Análise por nicho geral
        por_nicho = (df.groupby("nicho")
                     .agg({"lucro_liquido": "sum", "gross_profit": "sum", "order_id": "count", "quantity": "sum",
                           "total_value": "sum", "freight": "sum", "taxes": "sum", "cost": "sum",
                           "rentability": "mean", "profitability": "mean"})
                     .reset_index())
        por_nicho["participacao_faturamento"] = por_nicho["total_value"] / kpis_gerais["faturamento_total"] if kpis_gerais["faturamento_total"] != 0 else 0
        por_nicho["participacao_lucro"] = por_nicho["lucro_liquido"] / kpis_gerais["lucro_liquido_total"] if kpis_gerais["lucro_liquido_total"] != 0 else 0
        por_nicho["media_dia_valor"] = por_nicho["total_value"] / dias_totais
        por_nicho["media_dia_unidades"] = por_nicho["quantity"] / dias_totais
        por_nicho = limpar_df_para_json(por_nicho)

        # ------------------------------
        # Forecast ML
        df_forecast, conclusoes = predict_sales_for_df(df)
        df_forecast = limpar_df_para_json(df_forecast)

        # ------------------------------
        # Rankings
        top_30_ads = (df.groupby("ad")
                      .agg({"lucro_liquido": "sum", "gross_profit": "sum"})
                      .sort_values("lucro_liquido", ascending=False)
                      .head(30)
                      .reset_index())
        top_30_ads["skus"] = top_30_ads["ad"].apply(lambda ad: df[df["ad"] == ad]["sku"].unique().tolist())
        top_30_ads = limpar_df_para_json(top_30_ads)

        top_30_skus = (df.groupby("sku")
                       .agg({"lucro_liquido": "sum", "gross_profit": "sum"})
                       .sort_values("lucro_liquido", ascending=False)
                       .head(30)
                       .reset_index())
        top_30_skus = limpar_df_para_json(top_30_skus)

        top_15_por_nicho = (df.groupby(["nicho", "sku"])
                            .agg({"lucro_liquido": "sum", "gross_profit": "sum"})
                            .sort_values(["nicho", "lucro_liquido"], ascending=[True, False])
                            .groupby(level=0).head(15)
                            .reset_index())
        top_15_por_nicho = limpar_df_para_json(top_15_por_nicho)

        df_anuncios = (df.groupby(["ad", "sku"])
                       .agg({"lucro_liquido": "sum", "gross_profit": "sum", "quantity": "sum", "total_value": "sum"})
                       .reset_index()
                       .rename(columns={"quantity": "total_unidades", "total_value": "faturamento_total"}))
        df_anuncios = limpar_df_para_json(df_anuncios)

        # ------------------------------
        # Montar retorno
        retorno = {
            "periodo": {"inicio": start.strftime("%Y-%m-%d"), "fim": end.strftime("%Y-%m-%d")},
            "kpis_gerais": kpis_gerais,
            "relatorios": {
                "diario": relatorios_diarios,
                "diario_por_nicho": relatorios_diarios_por_nicho,
                "diario_anuncios": relatorios_diarios_anuncios
            },
            "analise": {
                "por_nicho": por_nicho.to_dict(orient="records"),
                "forecast": df_forecast.to_dict(orient="records"),
                "conclusoes_forecast": conclusoes
            },
            "rankings": {
                "top_30_ads": top_30_ads.to_dict(orient="records"),
                "top_30_skus": top_30_skus.to_dict(orient="records"),
                "top_15_por_nicho": top_15_por_nicho.to_dict(orient="records"),
                "anuncios_totais": df_anuncios.to_dict(orient="records")
            }
        }

        logger.info("Relatório flex gerado com sucesso")
        return retorno

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
    return {"mensagem": f"{deletados} registro(s) deletado(s)."}
# ------------------------------
# ROTAS REST DE ORDERS
@app.get("/orders")
def get_all_orders():
    """Retorna todos os pedidos do banco"""
    logger.info("Chamada para /orders: retornando todos os pedidos")
    try:
        db = app.state.database
        cursor = db.conn.cursor()
        query = "SELECT * FROM orders"
        linhas = cursor.execute(query).fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(linhas, columns=colunas)
        df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        logger.exception("Erro ao retornar todos os pedidos")
        return JSONResponse(status_code=500, content={"erro": str(e)})


import logging
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, WebSocket
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils.get_data import Data
from utils.data_parser import DataParser
from utils.database import Database, TableCreator
from utils.order_inserter import OrderInserter
from utils.sku_nicho_inserter import SkuNichoInserter
from utils.ml_utils import predict_sales_for_df

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
# LIFESPAN FASTAPI
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

    # ------------------------------
    # Scheduler para atualizar pedidos a cada 5 minutos
    scheduler = AsyncIOScheduler()
    
    def atualizar_pedidos_automatico():
        try:
            logger.info("Iniciando atualização automática de pedidos...")
            url = "https://app.arpcommerce.com.br/sells?r=" + datetime.today().strftime("%Y-%m-%d")
            cookies = {
                "session": ".eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aN60Hw.RO7_FgvILd3ILXDdIQHY9hdD4UE"
            }
            response = requests.get(url, cookies=cookies)
            response.raise_for_status()
            raw_json = response.json()
            logger.info(f"{len(raw_json)} pedidos brutos obtidos da API")

            parser = DataParser(raw_json)
            pedidos = parser.parse_orders()
            logger.info(f"{len(pedidos)} pedidos parseados")

            app.state.order_inserter.insert_orders(pedidos)
            logger.info(f"{len(pedidos)} pedidos inseridos no DB automaticamente")
        except Exception as e:
            logger.exception(f"Erro na atualização automática de pedidos: {e}")

    scheduler.add_job(atualizar_pedidos_automatico, 'interval', minutes=5)
    scheduler.start()
    logger.info("Scheduler iniciado: atualização automática a cada 5 minutos")
    # Atualiza imediatamente ao iniciar
    atualizar_pedidos_automatico()

    yield

    # ------------------------------
    scheduler.shutdown()
    database.close()
    logger.info("Database desconectada e lifespan finalizado")


app = FastAPI(lifespan=lifespan)

# ------------------------------
# Função para gerar relatório diário
def gerar_relatorio_diario(db: Database):
    try:
        cursor = db.conn.cursor()
        hoje = datetime.today().strftime("%Y-%m-%d")
        query = """SELECT o.*, n.nicho 
                   FROM orders o 
                   LEFT JOIN sku_nichos n ON o.sku = n.sku 
                   WHERE date(o.payment_date) = ?"""
        linhas = cursor.execute(query, (hoje,)).fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(linhas, columns=colunas)
        if df.empty:
            return {"mensagem": "Nenhuma venda hoje"}

        df["lucro_liquido"] = df["gross_profit"] - df["cost"] - df["freight"] - df["taxes"]
        df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")

        # Relatório por nicho
        nichos = []
        for nicho, grupo in df.groupby("nicho"):
            nichos.append({
                "nicho": nicho if nicho else "Sem nicho",
                "vendas_total": int(grupo["quantity"].sum()),
                "faturamento_total": float(grupo["total_value"].sum()),
                "ultima_venda": grupo.iloc[-1].to_dict()
            })

        # Melhor produto do dia
        melhor_produto = df.groupby("sku")["lucro_liquido"].sum().idxmax()
        melhor_produto_info = df[df["sku"] == melhor_produto].iloc[0].to_dict()

        # Melhor anúncio
        melhor_ad = df.groupby("ad")["lucro_liquido"].sum().idxmax()
        melhor_ad_info = df[df["ad"] == melhor_ad].iloc[0].to_dict()

        # Anúncios negativos
        anuncios_negativos = df[df["lucro_liquido"] < 0][["ad", "sku", "lucro_liquido"]].to_dict(orient="records")

        # Top 10 anúncios, vendas e skus
        top_ads = df.groupby("ad")["lucro_liquido"].sum().sort_values(ascending=False).head(10).reset_index().to_dict(orient="records")
        top_skus = df.groupby("sku")["lucro_liquido"].sum().sort_values(ascending=False).head(10).reset_index().to_dict(orient="records")
        top_vendas = df.sort_values("lucro_liquido", ascending=False).head(10).to_dict(orient="records")

        relatorio = {
            "data": hoje,
            "nichos": nichos,
            "melhor_produto": melhor_produto_info,
            "melhor_ad": melhor_ad_info,
            "anuncios_negativos": anuncios_negativos,
            "top_ads": top_ads,
            "top_skus": top_skus,
            "top_vendas": top_vendas
        }
        return relatorio
    except Exception as e:
        logger.exception(f"Erro ao gerar relatório diário: {e}")
        return {"erro": str(e)}

# ------------------------------
# WEBSOCKET DE RELATÓRIO DIÁRIO
connected_websockets = []

@app.websocket("/ws/relatorio_diario")
async def websocket_relatorio_diario(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    logger.info("WebSocket conectado")

    # Envia relatório inicial
    try:
        relatorio = gerar_relatorio_diario(app.state.database)
        await websocket.send_json(relatorio)
    except Exception as e:
        logger.exception(f"Erro ao enviar relatório inicial: {e}")

    # Mantém conexão aberta
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        connected_websockets.remove(websocket)
        logger.info("WebSocket desconectado")

# ------------------------------
# WATCHDOG PARA ALTERAÇÃO DO DB
class DBChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("database.db"):
            logger.info("DB modificado, enviando relatório para WS")
            relatorio = gerar_relatorio_diario(app.state.database)
            for ws in connected_websockets:
                try:
                    import asyncio
                    run_coroutine_threadsafe(ws.send_json(relatorio), asyncio.get_running_loop())
                except Exception as e:
                    logger.exception(f"Erro ao enviar WS: {e}")

observer = Observer()
observer.schedule(DBChangeHandler(), path=BASE_DIR, recursive=False)
observer.start()

def gerar_relatorio_diario(db: Database):
    try:
        cursor = db.conn.cursor()
        hoje = datetime.today().strftime("%Y-%m-%d")
        query = """SELECT o.*, n.nicho 
                   FROM orders o 
                   LEFT JOIN sku_nichos n ON o.sku = n.sku 
                   WHERE date(o.payment_date) = ?"""
        linhas = cursor.execute(query, (hoje,)).fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(linhas, columns=colunas)
        if df.empty:
            return {"mensagem": "Nenhuma venda hoje"}

        df["lucro_liquido"] = df["gross_profit"] - df["cost"] - df["freight"] - df["taxes"]
        df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
        df["payment_date"] = df["payment_date"].apply(lambda x: x.isoformat() if pd.notnull(x) else "")

        # Últimas 10 vendas
        ultimas_vendas = df.sort_values("payment_date", ascending=False).head(10).to_dict(orient="records")

        # Nichos
        nichos = []
        for nicho, grupo in df.groupby("nicho"):
            ult_venda = grupo.iloc[-1].to_dict()
            for k, v in ult_venda.items():
                if isinstance(v, pd.Timestamp):
                    ult_venda[k] = v.isoformat()
            nichos.append({
                "nicho": nicho if nicho else "Sem nicho",
                "vendas_total": int(grupo["quantity"].sum()),
                "faturamento_total": float(grupo["total_value"].sum()),
                "ultima_venda": ult_venda
            })

        melhor_produto_info = df.groupby("sku")["lucro_liquido"].sum().idxmax()
        melhor_produto_info = df[df["sku"] == melhor_produto_info].iloc[0].to_dict()
        for k, v in melhor_produto_info.items():
            if isinstance(v, pd.Timestamp):
                melhor_produto_info[k] = v.isoformat()

        melhor_ad_info = df.groupby("ad")["lucro_liquido"].sum().idxmax()
        melhor_ad_info = df[df["ad"] == melhor_ad_info].iloc[0].to_dict()
        for k, v in melhor_ad_info.items():
            if isinstance(v, pd.Timestamp):
                melhor_ad_info[k] = v.isoformat()

        anuncios_negativos = df[df["lucro_liquido"] < 0][["ad", "sku", "lucro_liquido"]].to_dict(orient="records")
        top_ads = df.groupby("ad")["lucro_liquido"].sum().sort_values(ascending=False).head(10).reset_index().to_dict(orient="records")
        top_skus = df.groupby("sku")["lucro_liquido"].sum().sort_values(ascending=False).head(10).reset_index().to_dict(orient="records")
        top_vendas = df.sort_values("lucro_liquido", ascending=False).head(10).to_dict(orient="records")
        for item in top_vendas:
            for k, v in item.items():
                if isinstance(v, pd.Timestamp):
                    item[k] = v.isoformat()

        relatorio = {
            "data": hoje,
            "nichos": nichos,
            "melhor_produto": melhor_produto_info,
            "melhor_ad": melhor_ad_info,
            "anuncios_negativos": anuncios_negativos,
            "top_ads": top_ads,
            "top_skus": top_skus,
            "top_vendas": top_vendas,
            "ultimas_10_vendas": ultimas_vendas
        }
        return relatorio
    except Exception as e:
        logger.exception(f"Erro ao gerar relatório diário: {e}")
        return {"erro": str(e)}

def on_modified(event):
    try:
        relatorio = gerar_relatorio_diario(db)
        loop = asyncio.get_event_loop()
        loop.create_task(ws.send_json(relatorio))
    except Exception as e:
        logger.exception(f"Erro ao enviar WS: {e}")