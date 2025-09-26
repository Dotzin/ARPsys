class OrderInserter:


    def __init__(self, db):
        """
        :param db: instância da classe Database
        """
        self.db = db

    def insert_orders(self, orders_list):
    
        for order in orders_list:
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
        self.db.commit()
