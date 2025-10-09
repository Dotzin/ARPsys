import requests
import logging
from typing import Optional, Any, Dict
from app.core.exceptions import APIException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class Data:
    def __init__(self, url: str, cookies: Optional[dict] = None, user_id: Optional[int] = None):
        self.url = url
        self.cookies = cookies or {}
        self.user_id = user_id
        if self.user_id:
            if '?' in self.url:
                self.url += f"&user_id={self.user_id}"
            else:
                self.url += f"?user_id={self.user_id}"
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Data inicializado com URL: {self.url}")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
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
            raise APIException(f"Failed to fetch data from {self.url}: {e}") from e
