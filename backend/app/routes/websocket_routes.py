from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.connection_manager import ConnectionManager
from app.services.report_service import ReportService
from app.core.container import container
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Rotas relacionadas a WebSocket
from fastapi import Query, WebSocketException, status
from app.core.dependencies import get_auth_service

@router.websocket("/ws/relatorio_diario")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    auth_service = get_auth_service()
    manager = container.connection_manager()
    manager.container = container  # Set container for periodic fetch
    report_service = container.report_service()

    logger.info(f"WebSocket connection attempt with token: {token[:10]}...")

    # Verify token and get username
    username = auth_service.verify_token(token)
    if username is None:
        logger.warning(f"Invalid token provided for WebSocket connection")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.info(f"Token verified for user: {username}")

    # Get user by username
    user = auth_service.get_user_by_username(username)
    if user is None:
        logger.warning(f"User not found for username: {username}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user.id
    logger.info(f"Connecting WebSocket for user_id: {user_id}")

    await manager.connect(user, websocket)
    logger.info(f"WebSocket connected for user {user_id}")
    try:
        # Envia o relatório atual imediatamente após a conexão
        try:
            current_report = report_service.get_daily_report_data(user_id=user_id)
            if current_report and current_report.get("status") == "sucesso":
                await websocket.send_json(
                    {"tipo": "relatorio_diario_inicial", "dados": current_report}
                )
                logger.info("Relatório inicial enviado para o novo cliente WebSocket.")
            else:
                logger.warning(f"Failed to get initial report for user {user_id}: {current_report}")
        except Exception as e:
            logger.exception(f"Error getting initial report for user {user_id}: {e}")

        # Mantém a conexão aberta esperando por mensagens (ou apenas para receber o broadcast)
        while True:
            # Apenas espera (pode receber pings/pongs ou mensagens do cliente, se necessário)
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erro inesperado no WebSocket para user {user_id}: {e}")
        manager.disconnect(websocket)
