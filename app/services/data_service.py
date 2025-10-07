import requests
import logging
from typing import Optional, Any, Dict


class Data:
    def __init__(self, url: str, cookies: Optional[dict] = None):
        self.url = url
        self.cookies = cookies or {}
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Data inicializado com URL: {self.url}")

    def get_data(self) -> Dict[str, Any]:
        try:
            self.logger.info(f"Fazendo requisição GET para {self.url}")
            response = requests.get(self.url, cookies=self.cookies)
            response.raise_for_status()
            self.logger.info(
                f"Requisição bem-sucedida. Status code: {response.status_code}"
            )
            return response.json()
        except requests.RequestException as e:
            self.logger.exception(f"Erro ao fazer requisição para {self.url}: {e}")
            raise
