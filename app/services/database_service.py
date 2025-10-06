import os
import logging
from app.repositories.database_repository import Database, TableCreator

class DatabaseService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.database = Database(db_path)
        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.logger.info(f"Conectando ao banco de dados em {self.db_path}")
        self.database.connect()

    def create_tables(self):
        self.logger.info("Criando tabelas no banco de dados")
        table_creator = TableCreator(self.database)
        table_creator.create_orders_table()
        table_creator.create_sku_nichos_table()
        self.logger.info("Tabelas criadas/verificadas com sucesso")

    def close(self):
        self.logger.info("Fechando conexão com o banco de dados")
        self.database.close()
