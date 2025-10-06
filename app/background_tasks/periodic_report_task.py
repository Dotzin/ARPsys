import asyncio
import logging
from datetime import datetime
from app.core.connection_manager import ConnectionManager
from app.services.data_service import Data
from app.services.data_parser_service import DataParser
from app.services.order_service import OrderInserter

logger = logging.getLogger(__name__)

class BackgroundTaskService:
    def __init__(self, app, manager, report_service, update_interval_seconds=300):
        self.app = app
        self.manager = manager
        self.report_service = report_service
        self.update_interval_seconds = update_interval_seconds
        self.current_daily_report = None
        self._task = None

    async def _periodic_update_and_broadcast(self):
        logger.info("Iniciando tarefa periódica de atualização e broadcast")
        while True:
            try:
                logger.info("Executando ciclo de atualização: obtendo pedidos...")
                # 1. Atualizar Pedidos (Chamada à API externa e inserção no DB)
                try:
                    data_inicio = data_fim = datetime.today().strftime("%Y-%m-%d")
                    url = f'https://app.arpcommerce.com.br/sells?r={data_inicio}'
                    headers = {'session': '.eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aMxLsg.3D5e5s_a96H1mPB_uHM7CySJ7n8'}

                    data_obj = Data(url, headers)
                    raw_json = data_obj.get_data()
                    logger.info(f"Dados brutos obtidos: {len(raw_json)} registros")

                    parser = DataParser(raw_json)
                    pedidos = parser.parse_orders()

                    # Inserção no banco de dados
                    self.app.state.order_inserter.insert_orders(pedidos)
                    logger.info(f"Ciclo de atualização: {len(pedidos)} pedidos inseridos/atualizados no DB.")
                except Exception as e:
                    logger.error(f"Falha na atualização de pedidos da API externa: {e}")
                    # Continua para o cálculo do relatório, que pode usar dados antigos

                # 2. Calcular o Relatório Diário
                relatorio = self.report_service.get_daily_report_data()

                # 3. Armazenar e fazer Broadcast
                if relatorio and relatorio.get("status") == "sucesso" and relatorio != self.current_daily_report:
                    self.current_daily_report = relatorio
                    await self.manager.broadcast({"tipo": "relatorio_diario", "dados": relatorio})
                    logger.info("Novo relatório diário calculado e transmitido via WebSocket.")
                elif relatorio and relatorio.get("status") == "sucesso":
                    logger.info("Relatório diário calculado, mas sem alterações desde a última verificação. Sem broadcast.")
                else:
                    logger.warning("Relatório diário não pôde ser calculado (sem dados ou erro). Sem broadcast.")

            except Exception as e:
                logger.exception("Erro fatal na tarefa periódica de atualização e broadcast")

            # 4. Esperar o próximo ciclo
            await asyncio.sleep(self.update_interval_seconds)

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._periodic_update_and_broadcast())
            logger.info("Tarefa de atualização periódica iniciada.")

    def stop(self):
        if self._task:
            self._task.cancel()
            logger.info("Tarefa de atualização periódica cancelada.")
