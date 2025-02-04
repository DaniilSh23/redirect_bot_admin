"""
Логика для работы с keitaro.
"""

# TODO: в качестве рефакторинга необходимо перенести сюда логику взаимодействия с кейтаро

import requests

from redirect_admin.services import RedirectBotSettingsService
from redirect_admin.exeptions import EmptySettingException
from redirect_bot_admin.settings import MY_LOGGER


class KeitaroAgent:
    """
    Агент для работы с Keitaro
    """
    headers = {
            "accept": "application/json",
            "Api-Key": "",
            "Content-Type": "application/json"
        }

    def __init__(self):
        """
        Конструктор класса, устанавливаем базовые аттрибуты.
        """
        self.keitaro_address = RedirectBotSettingsService.read(key="keitaro_main_domain")
        if not self.keitaro_address:
            raise EmptySettingException("keitaro_main_domain")
        self.keitaro_api_address = f"http://{self.keitaro_address}/admin_api/v1/"
        
        self.keitaro_api_key = RedirectBotSettingsService.read(key="keitaro_api_key")
        if not self.keitaro_address:
            raise EmptySettingException("keitaro_api_key")
        self.headers["Api-Key"] = self.keitaro_api_key
        
    def create_domain(self, domain) -> str | None:
        """
        Создание домена в keitaro. В случае успеха возвращает ID нового домена в Keitaro, иначе None.
        """
        req_url = f"{self.keitaro_api_address}domains"
        data = {
            "name": domain,
            "default_campaign_id": 0,
            "catch_not_found": True,
            "notes": "",
            "ssl_redirect": True,
            "allow_indexing": False,
            "admin_dashboard": False
        }

        response = requests.post(url=req_url, json=data, headers=self.headers)
        if response.status_code >= 400:
            MY_LOGGER.warning("Неудачный запрос к API Keitaro для создания нового домена")
            return None

        resp_data = response.json()
        return resp_data[0].get("id")


    def delete_domain(self, domain_keitaro_id) -> bool:
        """
        Удаление домена в keitaro. Возвращает булевое значение, как флаг успешно ли было удаление
        """
        req_url = f"{self.keitaro_api_address}domains/{domain_keitaro_id}"
        response = requests.delete(url=req_url, headers=self.headers)
        if response.status_code != 200:
            MY_LOGGER.warning(f"Неудачный запрос к API Keitaro для удаления домена | {response.status_code} | {response.json()}")
            return False
        MY_LOGGER.success(f"Успешный запрос к API Keitaro для удаления домена")
        return True
    