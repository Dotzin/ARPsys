import logging

logger = logging.getLogger(__name__)

class SkuNichoInserter:
    def __init__(self, db):
        self.db = db
        logger.info("SkuNichoInserter inicializado com sucesso")

    def insert_one(self, sku: str, nicho: str):
        try:
            logger.info(f"Inserindo SKU '{sku}' no nicho '{nicho}'")
            self.db.cursor.execute(
                "INSERT OR IGNORE INTO sku_nichos (sku, nicho) VALUES (?, ?)",
                (sku, nicho)
            )
            self.db.commit()
            logger.info(f"SKU '{sku}' inserido com sucesso")
        except Exception as e:
            logger.exception(f"Erro ao inserir SKU '{sku}': {e}")
            raise

    def insert_many(self, sku_nicho_list: list[dict]):
        try:
            logger.info(f"Inserindo {len(sku_nicho_list)} registros de SKU/nicho")
            values = [(item["sku"], item["nicho"]) for item in sku_nicho_list]
            self.db.cursor.executemany(
                "INSERT OR IGNORE INTO sku_nichos (sku, nicho) VALUES (?, ?)",
                values
            )
            self.db.commit()
            logger.info("Inserção múltipla concluída com sucesso")
        except Exception as e:
            logger.exception(f"Erro ao inserir múltiplos SKUs: {e}")
            raise

    def update_nicho(self, sku: str, new_nicho: str):
        try:
            logger.info(f"Atualizando SKU '{sku}' para o nicho '{new_nicho}'")
            self.db.cursor.execute(
                "UPDATE sku_nichos SET nicho = ? WHERE sku = ?",
                (new_nicho, sku)
            )
            self.db.commit()
            rowcount = self.db.cursor.rowcount
            logger.info(f"{rowcount} registro(s) atualizado(s)")
            return rowcount
        except Exception as e:
            logger.exception(f"Erro ao atualizar SKU '{sku}': {e}")
            raise

    def delete_sku(self, sku: str):
        try:
            logger.info(f"Deletando SKU '{sku}'")
            self.db.cursor.execute(
                "DELETE FROM sku_nichos WHERE sku = ?",
                (sku,)
            )
            self.db.commit()
            rowcount = self.db.cursor.rowcount
            logger.info(f"{rowcount} registro(s) deletado(s)")
            return rowcount
        except Exception as e:
            logger.exception(f"Erro ao deletar SKU '{sku}': {e}")
            raise

    def list_all(self):
        try:
            logger.info("Listando todos os SKUs")
            self.db.cursor.execute(
                "SELECT sku, nicho, created_at FROM sku_nichos"
            )
            rows = self.db.cursor.fetchall()
            logger.info(f"{len(rows)} registros retornados")
            return rows
        except Exception as e:
            logger.exception(f"Erro ao listar SKUs: {e}")
            raise
