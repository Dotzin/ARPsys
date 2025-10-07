import logging
from datetime import datetime, timedelta

class OrderInserter:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.logger.info("OrderInserter inicializado com sucesso")

    def insert_orders(self, orders_input):
        if isinstance(orders_input, list):
            orders_dict = {}
            for order in orders_input:
                cart_id = order.get('cart') or order.get('cart_id')
                if cart_id not in orders_dict:
                    orders_dict[cart_id] = []
                orders_dict[cart_id].append(order)
        elif isinstance(orders_input, dict):
            # Check if it's a single order dict
            if 'order_id' in orders_input or 'order' in orders_input:
                orders_input = [orders_input]
                orders_dict = {}
                for order in orders_input:
                    cart_id = order.get('cart') or order.get('cart_id')
                    if cart_id not in orders_dict:
                        orders_dict[cart_id] = []
                    orders_dict[cart_id].append(order)
            else:
                orders_dict = orders_input
        else:
            raise ValueError("orders_input deve ser uma lista ou um dicionário")

        total_pedidos = sum(len(v) for v in orders_dict.values())
        self.logger.info(f"Iniciando inserção de {total_pedidos} pedidos")
        inserted_count = 0

        for cart_key, orders in orders_dict.items():
            for order in orders:
                try:
                    order_id = order.get('order') or order.get('order_id')
                    cart_id = order.get('cart') or order.get('cart_id') or cart_key
                    payment_date_raw = order.get('payment_date')
                    payment_date_adj = None
                    if payment_date_raw:
                        try:
                            dt = datetime.strptime(payment_date_raw, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            dt = datetime.fromisoformat(payment_date_raw)
                        payment_date_adj = (dt - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                    self.db.cursor.execute("""
                        INSERT OR REPLACE INTO orders (
                            order_id, cart_id, ad, sku, title,
                            quantity, total_value, payment_date,
                            status, cost, gross_profit, taxes, freight,
                            committee, fraction, profitability, rentability,
                            store, profit
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        order_id, cart_id, order.get('ad'), order.get('sku'), order.get('title'),
                        order.get('quantity'), order.get('total_value'), payment_date_adj,
                        order.get('status'), order.get('cost', 0), order.get('gross_profit', 0),
                        order.get('taxes', 0), order.get('freight', 0), order.get('committee', 0),
                        order.get('fraction', 1), order.get('profitability', 0), order.get('rentability', 0),
                        order.get('store'), order.get('profit', 0)
                    ))
                    inserted_count += 1
                except Exception as e:
                    self.logger.exception(f"Erro ao inserir pedido {order.get('order') or order.get('order_id')}: {e}")
        try:
            self.db.commit()
            self.logger.info(f"Inserção concluída: {inserted_count}/{total_pedidos} pedidos inseridos")
        except Exception as e:
            self.logger.exception(f"Erro ao executar commit da inserção: {e}")
            raise
