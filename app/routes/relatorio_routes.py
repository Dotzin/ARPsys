from fastapi import APIRouter, Query, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import asyncio
from app.services.data_service import Data
from app.services.data_parser_service import DataParser
from app.services.order_service import OrderInserter
from app.services.report_service import ReportService
from app.core.connection_manager import ConnectionManager
from app.background_tasks.periodic_report_task import BackgroundTaskService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency injection for services
def get_order_inserter(request: Request) -> OrderInserter:
    return request.app.state.order_inserter

def get_report_service(request: Request) -> ReportService:
    return request.app.state.report_service

def get_connection_manager(request: Request) -> ConnectionManager:
    return request.app.state.connection_manager

# ROTA: Atualiza pedidos da API (Com Broadcast)
@router.post("/atualizar_pedidos")
async def atualizar_pedidos(
    data: str = Query(None, description="Data única DD/MM/YYYY ou intervalo DD/MM/YYYY/DD/MM/YYYY"),
    inserter: OrderInserter = Depends(get_order_inserter),
    report_service: ReportService = Depends(get_report_service),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    logger.info(f"Chamada para /atualizar_pedidos com data={data}")
    try:
        if not data:
            # Ajustar para o fuso horário da API (UTC, BRT é UTC-3)
            # Se hora < 21, enviar hoje, senão amanhã
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
                data_ajustada = datetime(int(ano), int(mes), int(dia)) + timedelta(days=1)
                data_inicio = data_fim = data_ajustada.strftime("%Y-%m-%d")
            elif len(partes) == 6:
                dia1, mes1, ano1, dia2, mes2, ano2 = partes
                data_inicio_ajustada = datetime(int(ano1), int(mes1), int(dia1)) + timedelta(days=1)
                data_fim_ajustada = datetime(int(ano2), int(mes2), int(dia2)) + timedelta(days=1)
                data_inicio = data_inicio_ajustada.strftime("%Y-%m-%d")
                data_fim = data_fim_ajustada.strftime("%Y-%m-%d")
            else:
                logger.warning("Formato de data inválido")
                return {"erro": "Formato de data inválido. Use DD/MM/YYYY ou DD/MM/YYYY/DD/MM/YYYY."}

        url = f'https://app.arpcommerce.com.br/sells?r={data_inicio}' if data_inicio == data_fim else f'https://app.arpcommerce.com.br/sells?r={data_inicio}/{data_fim}'
        logger.info(f"URL gerada para API externa: {url}")

        # ATENÇÃO: Credenciais estáticas, use variáveis de ambiente em produção
        data_obj = Data(url, {'session': '.eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aMxLsg.3D5e5s_a96H1mPB_uHM7CySJ7n8'})
        raw_json = data_obj.get_data()
        logger.info(f"Dados brutos obtidos: {len(raw_json)} registros")

        parser = DataParser(raw_json)
        pedidos = parser.parse_orders()
        logger.info(f"Pedidos parseados: {len(pedidos)} pedidos")

        inserter.insert_orders(pedidos)
        logger.info(f"{len(pedidos)} pedidos inseridos no DB com sucesso")

        # --- ATUALIZAÇÃO MANUAL APÓS REQUISIÇÃO ---
        # Recalcula o relatório e faz broadcast após uma atualização manual
        novo_relatorio = report_service.get_daily_report_data()
        if novo_relatorio and novo_relatorio.get("status") == "sucesso":
            # Cria uma task para o broadcast para não bloquear a resposta HTTP
            asyncio.create_task(manager.broadcast({"tipo": "relatorio_diario", "dados": novo_relatorio}))
            logger.info("Broadcast após atualização manual da API.")

        # ----------------------------------------------------

        return {"mensagem": f"{len(pedidos)} pedidos atualizados com sucesso.", "data_inicio": data_inicio, "data_fim": data_fim}

    except Exception as e:
        logger.exception("Erro ao atualizar pedidos")
        return JSONResponse(status_code=500, content={"erro": str(e)})

# RELATÓRIO FLEX (ML + KPIs + Rankings)
@router.get("/relatorio_flex")
def relatorio_flex(
    data_inicio: str = None,
    data_fim: str = None,
    report_service: ReportService = Depends(get_report_service)
):
    try:
        return report_service.generate_relatorio_flex(data_inicio, data_fim)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"erro": str(e)})
    except Exception as e:
        logger.exception("Erro ao gerar relatório flex")
        return JSONResponse(status_code=500, content={"erro": str(e)})
