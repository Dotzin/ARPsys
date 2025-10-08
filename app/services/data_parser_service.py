import logging
from app.core.exceptions import ValidationException

class DataParser:
    def __init__(self, raw_data: dict):
        self.raw_data = raw_data
        self.logger = logging.getLogger(__name__)
        self.logger.info("DataParser inicializado com dados brutos")

    def parse_orders(self):
        orders_list = []
        total_orders = 0
        try:
            if isinstance(self.raw_data, dict):
                for cart_id, orders in self.raw_data.items():
                    for order in orders:
                        orders_list.append({
                            "order_id": order["order"],
                            "cart_id": cart_id,
                            "ad": order["ad"],
                            "sku": order["sku"],
                            "profit": order["profit"],
                            "title": order["title"],
                            "quantity": order["quantity"],
                            "total_value": order["total_value"],
                            "payment_date": order["payment_date"],
                            "status": order["status"],
                            "cost": order.get("cost", 0),
                            "gross_profit": order.get("gross_profit", 0),
                            "taxes": order.get("taxes", 0),
                            "freight": order.get("freight", 0),
                            "committee": order.get("committee", 0),
                            "fraction": order.get("fraction", 1),
                            "profitability": order.get("profitability", 0),
                            "rentability": order.get("rentability", 0),
                            "store": order["store"]
                        })
                        total_orders += 1
            elif isinstance(self.raw_data, list):
                for order in self.raw_data:
                    orders_list.append({
                        "order_id": order.get("order", ""),
                        "cart_id": order.get("cart", ""),
                        "ad": order.get("ad", ""),
                        "sku": order.get("sku", ""),
                        "profit": order.get("profit", 0),
                        "title": order.get("title", ""),
                        "quantity": order.get("quantity", 0),
                        "total_value": order.get("total_value", 0),
                        "payment_date": order.get("payment_date", ""),
                        "status": order.get("status", ""),
                        "cost": order.get("cost", 0),
                        "gross_profit": order.get("gross_profit", 0),
                        "taxes": order.get("taxes", 0),
                        "freight": order.get("freight", 0),
                        "committee": order.get("committee", 0),
                        "fraction": order.get("fraction", 1),
                        "profitability": order.get("profitability", 0),
                        "rentability": order.get("rentability", 0),
                        "store": order.get("store", 0)
                    })
                    total_orders += 1
            self.logger.info(f"Parse concluído: {total_orders} pedidos extraídos")
        except Exception as e:
            self.logger.exception(f"Erro ao parsear pedidos: {e}")
            raise ValidationException(f"Failed to parse order data: {e}") from e
        return orders_list
