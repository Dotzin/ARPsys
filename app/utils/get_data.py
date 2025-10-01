import requests
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class Data:
    def __init__(self, url: str, cookies: dict = None):
        self.url = url
        self.cookies = cookies or {}
        logger.info(f"Data inicializado com URL: {self.url}")

    def get_data(self):
        try:
            logger.info(f"Fazendo requisição GET para {self.url}")
            response = requests.get(self.url, cookies=self.cookies)
            response.raise_for_status()
            logger.info(f"Requisição bem-sucedida. Status code: {response.status_code}")
            return response.json()
        except requests.RequestException as e:
            logger.exception(f"Erro ao fazer requisição para {self.url}: {e}")
            raise
