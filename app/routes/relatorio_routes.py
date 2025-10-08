from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import asyncio
from app.services.data_service import Data
from app.services.data_parser_service import DataParser
from app.services.order_service import OrderInserter
from app.services.report_service import ReportService
from app.core.connection_manager import ConnectionManager
from app.models import DateRangeQuery, ReportQuery
from app.config.settings import settings
from app.core.container import container
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ROUTE: Update orders from API (With Broadcast)
@router.post("/atualizar_pedidos")
async def atualizar_pedidos(
    query: DateRangeQuery = Depends(),
    inserter: OrderInserter = Depends(lambda: container.order_inserter()),
    report_service: ReportService = Depends(lambda: container.report_service()),
    manager: ConnectionManager = Depends(lambda: container.connection_manager()),
):
    logger.info(f"Chamada para /atualizar_pedidos com data={query.data}")
    try:
        data = query.data
        if not data:
            # Adjust for API timezone (UTC, BRT is UTC-3)
            # If hour < 21, send today, else tomorrow
            agora = datetime.now()
            if agora.hour < 21:
                data_ajustada = agora
            else:
                data_ajustada = agora + timedelta(days=1)
            data_inicio = data_fim = data_ajustada.strftime("%Y-%m-%d")
        else:
            partes = data.split("/")
            if len(partes) == 3:
                dia, mes, ano = partes
                data_ajustada = datetime(int(ano), int(mes), int(dia)) + timedelta(
                    days=1
                )
                data_inicio = data_fim = data_ajustada.strftime("%Y-%m-%d")
            elif len(partes) == 6:
                dia1, mes1, ano1, dia2, mes2, ano2 = partes
                data_inicio_ajustada = datetime(
                    int(ano1), int(mes1), int(dia1)
                ) + timedelta(days=1)
                data_fim_ajustada = datetime(
                    int(ano2), int(mes2), int(dia2)
                ) + timedelta(days=1)
                data_inicio = data_inicio_ajustada.strftime("%Y-%m-%d")
                data_fim = data_fim_ajustada.strftime("%Y-%m-%d")
            else:
                logger.warning("Formato de data inválido")
                return {
                    "erro": "Formato de data inválido. Use DD/MM/YYYY ou DD/MM/YYYY/DD/MM/YYYY."
                }

        url = (
            f"https://app.arpcommerce.com.br/sells?r={data_inicio}"
            if data_inicio == data_fim
            else f"https://app.arpcommerce.com.br/sells?r={data_inicio}/{data_fim}"
        )
        logger.info(f"URL gerada para API externa: {url}")

        session_token = settings.api_session_token
        data_obj = Data(url, {"session": session_token})
        raw_json = data_obj.get_data()
        logger.info(f"Dados brutos obtidos: {len(raw_json)} registros")

        parser = DataParser(raw_json)
        pedidos = parser.parse_orders()
        logger.info(f"Pedidos parseados: {len(pedidos)} pedidos")

        inserter.insert_orders(pedidos)
        logger.info(f"{len(pedidos)} pedidos inseridos no DB com sucesso")

        # --- MANUAL UPDATE AFTER REQUEST ---
        # Recalculates the report and broadcasts after a manual update
        novo_relatorio = report_service.get_daily_report_data()
        if novo_relatorio and novo_relatorio.get("status") == "sucesso":
            # Creates a task for broadcast to not block HTTP response
            asyncio.create_task(
                manager.broadcast({"tipo": "relatorio_diario", "dados": novo_relatorio})
            )
            logger.info("Broadcast after manual API update.")

        # ----------------------------------------------------

        return {
            "mensagem": f"{len(pedidos)} pedidos atualizados com sucesso.",
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }

    except Exception as e:
        logger.exception("Erro ao atualizar pedidos")
        return JSONResponse(status_code=500, content={"erro": str(e)})


# RELATÓRIO FLEX (ML + KPIs + Rankings)
@router.get("/relatorio_flex")
def relatorio_flex(
    query: ReportQuery = Depends(),
    report_service: ReportService = Depends(lambda: container.report_service()),
):
    try:
        return report_service.generate_relatorio_flex(query.data_inicio, query.data_fim)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"erro": str(e)})
    except Exception as e:
        logger.exception("Erro ao gerar relatório flex")
        return JSONResponse(status_code=500, content={"erro": str(e)})
