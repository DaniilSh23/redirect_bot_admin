"""
Сервисы для взаимодействия с БД.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from redirect_admin.models import RedirectBotSettings, TlgUser, UserDomains
from redirect_bot_admin.settings import MY_LOGGER


class UserDomainService:
    """
    Сервис для взаимодействия с доменами пользователей.
    """
    
    @staticmethod
    def create(user_tlg_id: int, domain: str) -> UserDomains | None:
        """
        Создание домена пользователя
        """
        tlg_user = TlgUserService.get_by_tlg_id(tlg_id=user_tlg_id)
        if not tlg_user:
            return False
        
        try:
            return UserDomains.objects.create(tlg_id=tlg_user, domain=domain)
        except Exception as err:
            MY_LOGGER.warning(f"Ошибка при создании новой записи UserDomains | {err}")

    @staticmethod
    def read(pk: int):
        """
        Получение домена пользователя
        """
        return get_object_or_404(UserDomains, pk=pk)

    @staticmethod
    def read_all_for_user(tlg_id: int):
        """
        Получение всех доменов пользователя
        """
        tlg_user = TlgUserService.get_by_tlg_id(tlg_id=tlg_id)
        if not tlg_user:
            return []
        return UserDomains.objects.filter(tlg_user=tlg_user)

    @staticmethod
    def delete(record: UserDomains):
        """
        Удаление домена пользователя
        """
        record.delete()


class RedirectBotSettingsService:
    """
    Сервис для взаимодействия с таблицей настроек.
    """

    @staticmethod
    def read(key: str):
        """
        Получение значений из таблицы настроек по ключу
        """
        try:
            return RedirectBotSettings.objects.get(key=key).value
        except ObjectDoesNotExist:
            MY_LOGGER.error(f"Ключ {key} не установлен в настройках!")
            return None
        

class TlgUserService:
    """
    Сервис для работы с моделью TlgUser
    """
    @staticmethod
    def get_by_tlg_id(tlg_id: int):
        """
        Получение объекта TlgUser по tlg_id.
        """
        try:
            TlgUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f"Не найден юзер с tlg_id == {tlg_id}")
            return None
