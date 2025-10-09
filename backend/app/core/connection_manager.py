import logging
import asyncio
from datetime import datetime, timedelta
from fastapi import WebSocket
from typing import List, Dict, Any
from app.services.data_service import Data
from app.services.data_parser_service import DataParser
from app.models import User


class ConnectionManager:
    def __init__(self, logger: logging.Logger):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.tasks: Dict[int, asyncio.Task] = {}
        self.logger = logger
        self.container = None  # Will be set from WS route

    async def connect(self, user: User, websocket: WebSocket):
        await websocket.accept()
        user_id = user.id
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        self.logger.info(
            f"Nova conexão WebSocket para usuário {user_id}. Total conexões: {total_connections}"
        )
        # Start periodic fetch if first connection for this user
        if len(self.active_connections[user_id]) == 1:
            self.tasks[user_id] = asyncio.create_task(self.fetch_task(user))

    def disconnect(self, websocket: WebSocket):
        for user_id, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.active_connections[user_id]
                    # Cancel task
                    if user_id in self.tasks:
                        self.tasks[user_id].cancel()
                        del self.tasks[user_id]
                total_connections = sum(len(conns) for conns in self.active_connections.values())
                self.logger.info(
                    f"Conexão WebSocket encerrada para usuário {user_id}. Total conexões: {total_connections}"
                )
                break

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        self.logger.info(
            f"Broadcast enviado para {total_connections} conexões: {message.get('tipo')}"
        )
        for user_id, connections in list(self.active_connections.items()):
            for connection in list(connections):
                try:
                    await connection.send_json(message)
                except RuntimeError as e:
                    self.logger.warning(f"Erro ao enviar broadcast para uma conexão: {e}")
                    self.disconnect(connection)
                except Exception as e:
                    self.logger.error(f"Erro inesperado ao enviar broadcast: {e}")
                    self.disconnect(connection)

    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]):
        if user_id in self.active_connections:
            self.logger.info(
                f"Broadcast para usuário {user_id} enviado para {len(self.active_connections[user_id])} conexões: {message.get('tipo')}"
            )
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                except RuntimeError as e:
                    self.logger.warning(f"Erro ao enviar broadcast para uma conexão: {e}")
                    self.disconnect(connection)
                except Exception as e:
                    self.logger.error(f"Erro inesperado ao enviar broadcast: {e}")
                    self.disconnect(connection)

    async def fetch_task(self, user: User):
        while True:
            await asyncio.sleep(180)  # 3 minutes
            try:
                session_token = user.api_session_token
                if not session_token:
                    self.logger.warning(f"Usuário {user.id} não tem session_token")
                    continue

                # Date logic: if hour < 21, today, else tomorrow
                agora = datetime.now()
                if agora.hour < 21:
                    data_ajustada = agora
                else:
                    data_ajustada = agora + timedelta(days=1)
                data_inicio = data_fim = data_ajustada.strftime("%Y-%m-%d")

                url = f"https://app.arpcommerce.com.br/sells?r={data_inicio}"
                self.logger.info(f"Buscando pedidos para usuário {user.id} em {data_inicio}")

                data_obj = Data(url, {"session": session_token})
                raw_json = data_obj.get_data()
                self.logger.info(f"Dados obtidos: {len(raw_json)} registros")

                parser = DataParser(raw_json)
                pedidos = parser.parse_orders()
                self.logger.info(f"Pedidos parseados: {len(pedidos)}")

                if self.container:
                    inserter = self.container.order_inserter()
                    inserter.insert_orders(pedidos, user.id)
                    self.logger.info(f"{len(pedidos)} pedidos inseridos para usuário {user.id}")

                    # Update report and broadcast
                    report_service = self.container.report_service()
                    report = report_service.get_daily_report_data(user.id)
                    if report and report.get("status") == "sucesso":
                        await self.broadcast_to_user(user.id, {"tipo": "relatorio_diario", "dados": report})
                        self.logger.info(f"Relatório atualizado enviado para usuário {user.id}")
            except Exception as e:
                self.logger.exception(f"Erro na busca periódica para usuário {user.id}: {e}")
