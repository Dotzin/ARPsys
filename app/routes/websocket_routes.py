from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.connection_manager import ConnectionManager
from app.services.report_service import ReportService
from app.core.container import container
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Rotas relacionadas a WebSocket
@router.websocket("/ws/relatorio_diario")
async def websocket_endpoint(websocket: WebSocket):
    manager = container.connection_manager()
    report_service = container.report_service()
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
