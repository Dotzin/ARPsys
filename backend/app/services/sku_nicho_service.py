import logging


class SkuNichoInserter:
    def __init__(self, database):
        self.db = database
        self.logger = logging.getLogger(__name__)
        self.logger.info("SkuNichoInserter inicializado com sucesso")

    def insert_one(self, sku: str, nicho: str, user_id: int = 1):
        try:
            self.logger.info(f"Inserindo SKU '{sku}' no nicho '{nicho}' para user {user_id}")
            self.db.cursor.execute(
                "INSERT OR IGNORE INTO sku_nichos (sku, nicho, user_id) VALUES (?, ?, ?)",
                (sku, nicho, user_id),
            )
            self.db.commit()
            self.logger.info(f"SKU '{sku}' inserido com sucesso")
        except Exception as e:
            self.logger.exception(f"Erro ao inserir SKU '{sku}': {e}")
            raise

    def insert_many(self, sku_nicho_list: list[dict], user_id: int = 1):
        try:
            self.logger.info(f"Inserindo {len(sku_nicho_list)} registros de SKU/nicho para user {user_id}")
            values = [(item["sku"], item["nicho"], user_id) for item in sku_nicho_list]
            self.db.cursor.executemany(
                "INSERT OR IGNORE INTO sku_nichos (sku, nicho, user_id) VALUES (?, ?, ?)", values
            )
            self.db.commit()
            self.logger.info("Inserção múltipla concluída com sucesso")
        except Exception as e:
            self.logger.exception(f"Erro ao inserir múltiplos SKUs: {e}")
            raise

    def update_nicho(self, sku: str, new_nicho: str, user_id: int = 1):
        try:
            self.logger.info(f"Atualizando SKU '{sku}' para o nicho '{new_nicho}' para user {user_id}")
            self.db.cursor.execute(
                "UPDATE sku_nichos SET nicho = ? WHERE sku = ? AND user_id = ?", (new_nicho, sku, user_id)
            )
            self.db.commit()
            rowcount = self.db.cursor.rowcount
            self.logger.info(f"{rowcount} registro(s) atualizado(s)")
            return rowcount
        except Exception as e:
            self.logger.exception(f"Erro ao atualizar SKU '{sku}': {e}")
            raise

    def delete_sku(self, sku: str, user_id: int = 1):
        try:
            self.logger.info(f"Deletando SKU '{sku}' para user {user_id}")
            self.db.cursor.execute("DELETE FROM sku_nichos WHERE sku = ? AND user_id = ?", (sku, user_id))
            self.db.commit()
            rowcount = self.db.cursor.rowcount
            self.logger.info(f"{rowcount} registro(s) deletado(s)")
            return rowcount
        except Exception as e:
            self.logger.exception(f"Erro ao deletar SKU '{sku}': {e}")
            raise

    def list_all(self, user_id: int = 1):
        try:
            self.logger.info(f"Listando todos os SKUs para user {user_id}")
            self.db.cursor.execute("SELECT sku, nicho FROM sku_nichos WHERE user_id = ?", (user_id,))
            rows = self.db.cursor.fetchall()
            self.logger.info(f"{len(rows)} registros retornados")
            return rows
        except Exception as e:
            self.logger.exception(f"Erro ao listar SKUs: {e}")
            raise
