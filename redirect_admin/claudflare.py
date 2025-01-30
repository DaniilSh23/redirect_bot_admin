"""
Модуль для работы с ClaudFlare
"""

import requests

from redirect_bot_admin.settings import MY_LOGGER


class ClaudFlareAgent:
    """
    Класс, который реализует логику взаимодействия с API ClaudFlare.
    """

    base_cloudflare_url = "https://api.cloudflare.com/"

    def __init__(self, claudflare_email, claudlare_api_key):
        """
        Конструктор класса.
        :param claudflare_email: str - EMAIL аккаунта Claudflare
        :param claudlare_api_key: str - Global API Key из ЛК Claudflare
        """

        self.claudflare_email = claudflare_email
        self.claudlare_api_key = claudlare_api_key

    def create_zone(self):
        """
        Создание зоны (привязка домена) ClaudFlare. Возвращает bool, как флаг успеха,
        устанавливает на класс new_zone_id - ID созданной зоны (домена) в ClaudFlare.
        """

        req_url = f"{self.base_cloudflare_url}client/v4/zones"
        req_headers = {
            "Content-Type": "application/json",
            "X-Auth-Email": self.claudflare_email,
            "X-Auth-Key": self.claudlare_api_key,
        }
        req_data = {"name": self.domain_name, "type": "full"}
        response = requests.post(url=req_url, headers=req_headers, json=req_data)
        if response.status_code != 200:
            MY_LOGGER.warning(
                f"Не удалось создать зону в ClaudFlare. Ответ: status == {response.status_code} | {response.json()}"
            )
            return False
        json_resp = response.json()

        claud_result = json_resp.get("result")
        if claud_result:
            self.new_zone_id = claud_result.get("id")
            return True
        else:
            return False

    def set_dns_for_new_zone(self, ip_for_a_record: str) -> bool:
        """
        Установка DNS А-записей во вновь созданную зону (подключенный домен)
        :param ip_for_a_record: str - IP адрес для установки в А-запись для новой зоны (домена) ClaudFlare.
        """
        req_url = (
            f"{self.base_cloudflare_url}client/v4/zones/{self.new_zone_id}/dns_records"
        )
        req_headers = {
            "Content-Type": "application/json",
            "X-Auth-Email": self.claudflare_email,
            "X-Auth-Key": self.claudlare_api_key,
        }
        req_data = {
            "comment": "FROM REDIRECT BOT WITH LOVE",
            "content": ip_for_a_record,
            "name": "@",
            "proxied": True,
            "ttl": 3600,
            "type": "A",
        }
        response = requests.post(url=req_url, headers=req_headers, json=req_data)
        if response.status_code != 200:
            MY_LOGGER.warning(
                f"Не удалось добавить DNS А-запись в новую зону ClaudFlare. Ответ: status == {response.status_code} | {response.json()}"
            )
            return False
        
        return True
    