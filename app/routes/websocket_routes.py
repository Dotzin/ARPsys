from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from app.core.connection_manager import ConnectionManager
from app.services.report_service import ReportService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Dependency injection for services
def get_connection_manager(request: Request) -> ConnectionManager:
    return request.app.state.connection_manager


def get_report_service(request: Request) -> ReportService:
    return request.app.state.report_service


# Rotas relacionadas a WebSocket
@router.websocket("/ws/relatorio_diario")
async def websocket_endpoint(websocket: WebSocket):
    manager = websocket.app.state.connection_manager
    report_service = websocket.app.state.report_service
    await manager.connect(websocket)
    try:
        # Envia o relatório atual imediatamente após a conexão
        current_report = report_service.get_daily_report_data()
        if current_report and current_report.get("status") == "sucesso":
            await websocket.send_json(
                {"tipo": "relatorio_diario_inicial", "dados": current_report}
            )
            logger.info("Relatório inicial enviado para o novo cliente WebSocket.")

        # Mantém a conexão aberta esperando por mensagens (ou apenas para receber o broadcast)
        while True:
            # Apenas espera (pode receber pings/pongs ou mensagens do cliente, se necessário)
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erro inesperado no WebSocket: {e}")
        manager.disconnect(websocket)
