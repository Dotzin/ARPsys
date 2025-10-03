import logging

logger = logging.getLogger(__name__)

class OrderInserter:
    def __init__(self, db):
        self.db = db
        logger.info("OrderInserter inicializado com sucesso")

    def insert_orders(self, orders_list):
        logger.info(f"Iniciando inserção de {len(orders_list)} pedidos")
        inserted_count = 0
        try:
            for order in orders_list:
                try:
                    self.db.cursor.execute("""
                        INSERT OR IGNORE INTO orders (
                            order_id, cart_id, ad, sku, title,
                            quantity, total_value, payment_date,
                            status, cost, gross_profit, taxes, freight,
                            committee, fraction, profitability, rentability,
                            store
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        order['order_id'],
                        order['cart_id'],
                        order['ad'],
                        order['sku'],
                        order['title'],
                        order['quantity'],
                        order['total_value'],
                        order['payment_date'],
                        order['status'],
                        order.get('cost', 0),
                        order.get('gross_profit', 0),
                        order.get('taxes', 0),
                        order.get('freight', 0),
                        order.get('committee', 0),
                        order.get('fraction', 1),
                        order.get('profitability', 0),
                        order.get('rentability', 0),
                        order['store']
                    ))
                    inserted_count += 1
                except Exception as e:
                    logger.exception(f"Erro ao inserir pedido {order.get('order_id')}: {e}")
            self.db.commit()
            logger.info(f"Inserção concluída: {inserted_count}/{len(orders_list)} pedidos inseridos")
        except Exception as e:
            logger.exception(f"Erro ao executar commit da inserção: {e}")
            raise
