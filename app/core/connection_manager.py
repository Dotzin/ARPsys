import logging
from fastapi import WebSocket
from typing import List, Dict, Any

class ConnectionManager:
    def __init__(self, logger: logging.Logger):
        self.active_connections: List[WebSocket] = []
        self.logger = logger

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"Nova conexão WebSocket. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.logger.info(f"Conexão WebSocket encerrada. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        self.logger.info(f"Broadcast enviado para {len(self.active_connections)} conexões: {message.get('tipo')}")
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except RuntimeError as e:
                self.logger.warning(f"Erro ao enviar broadcast para uma conexão: {e}")
                self.disconnect(connection)
            except Exception as e:
                self.logger.error(f"Erro inesperado ao enviar broadcast: {e}")
                self.disconnect(connection)
