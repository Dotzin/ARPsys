import asyncio
import logging
from datetime import datetime, timedelta
from app.core.connection_manager import ConnectionManager
from app.services.data_service import Data
from app.services.data_parser_service import DataParser
from app.services.order_service import OrderInserter
from app.config.settings import settings

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
                # 1. Update Orders (Call to external API and DB insertion)
                try:
                    logger.info("Starting order update from external API.")
                    # Get all users with integration of type 'arp'
                    integration_service = self.app.state.container.integrations_service()
                    arp_integrations = integration_service.get_integrations_by_type('arpcommerce')
                    logger.info(f"Encontradas {len(arp_integrations)} integrações 'arpcommerce': {[i['user_id'] for i in arp_integrations]}")
                    logger.info(f"Atualizando pedidos para {len(arp_integrations)} usuários com integração 'arpcommerce'")

                    if not arp_integrations:
                        logger.info("Nenhum usuário com integração 'arpcommerce' encontrada. Pulando atualização de pedidos e cálculo de relatório.")
                        return  # Skip the rest of the cycle
                    else:
                        # Adjust for API timezone (UTC, BRT is UTC-3)
                        # If hour < 21, send today, else tomorrow
                        agora = datetime.now()
                        if agora.hour < 21:
                            data_ajustada = agora
                        else:
                            data_ajustada = agora + timedelta(days=1)
                        data_inicio = data_fim = data_ajustada.strftime("%Y-%m-%d")
                        logger.info(f"Data ajustada para requisição: {data_inicio}")
                        url = f"https://app.arpcommerce.com.br/sells?r={data_inicio}"

                        total_orders = 0
                        for integration in arp_integrations:
                            user_id = integration['user_id']
                            session_token = integration['token_value']
                            headers = {"session": session_token}
                            try:
                                logger.info(f"Fazendo requisição para URL: {url} para usuário {user_id}")
                                data_obj = Data(url, headers, user_id=user_id)
                                raw_json = data_obj.get_data()
                                logger.info(
                                    f"Requisição concluída para usuário {user_id}. Dados brutos obtidos: {len(raw_json)} registros"
                                )

                                parser = DataParser(raw_json)
                                pedidos = parser.parse_orders()
                                logger.info(f"Pedidos parseados para usuário {user_id}: {len(pedidos)} pedidos")

                                # Database insertion
                                self.app.state.container.order_inserter().insert_orders(pedidos, user_id=user_id)
                                total_orders += len(pedidos)
                                logger.info(
                                    f"Update cycle for user {user_id}: {len(pedidos)} orders inserted/updated in DB."
                                )
                            except Exception as e:
                                logger.error(f"Failed to update orders for user {user_id}: {e}")

                        logger.info(f"Total orders updated across all users: {total_orders}")

                except Exception as e:
                    logger.error(f"Failed to update orders from external API: {e}")
                    # Continues to report calculation, which can use old data

                # 2. Calculate Daily Report
                relatorio = self.report_service.get_daily_report_data()

                # 3. Store and Broadcast
                if (
                    relatorio
                    and relatorio.get("status") == "sucesso"
                    and relatorio != self.current_daily_report
                ):
                    self.current_daily_report = relatorio
                    await self.manager.broadcast(
                        {"tipo": "relatorio_diario", "dados": relatorio}
                    )
                    logger.info(
                        "New daily report calculated and broadcasted via WebSocket."
                    )
                elif relatorio and relatorio.get("status") == "sucesso":
                    logger.info(
                        "Daily report calculated, but no changes since last check. No broadcast."
                    )
                else:
                    logger.warning(
                        "Daily report could not be calculated (no data or error). No broadcast."
                    )

            except Exception as e:
                logger.exception(
                    "Erro fatal na tarefa periódica de atualização e broadcast"
                )

            # 4. Wait for next cycle
            await asyncio.sleep(self.update_interval_seconds)

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._periodic_update_and_broadcast())
            logger.info("Tarefa de atualização periódica iniciada.")

    def stop(self):
        if self._task:
            self._task.cancel()
            logger.info("Tarefa de atualização periódica cancelada.")
