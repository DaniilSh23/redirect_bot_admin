"""
Сервисы для взаимодействия с БД.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from redirect_admin.models import LinkSet, Links, Payments, RedirectBotSettings, TlgUser, Transaction, UserDomains
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
            return UserDomains.objects.create(tlg_user=tlg_user, domain=domain)
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
    def get_by_tlg_id(tlg_id):
        """
        Получение объекта TlgUser по tlg_id.
        """
        try:
            return TlgUser.objects.get(tlg_id=tlg_id)
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f"Не найден юзер с tlg_id == {tlg_id}")
            return None


class TransferUserService:
    """
    Сервис для переноса данных с одного аккаунта на другой.
    """

    @staticmethod
    def transfer(old_tlg_id, new_tlg_id):
        """
        Выполняем трансфер данных между аккаунтами.
        """
        old_user = TlgUserService.get_by_tlg_id(tlg_id=old_tlg_id)
        if not old_user:
            MY_LOGGER.warning(f"Перенос данных аккаунтов не удался. Не найден юзер с tlg_id == {old_tlg_id}")
            return False

        new_user = TlgUserService.get_by_tlg_id(tlg_id=new_tlg_id)
        if not old_user:
            MY_LOGGER.warning(f"Перенос данных аккаунтов не удался. Не найден юзер с tlg_id == {old_tlg_id}")
            return False

        TransferUserService.transfer_links(old_user, new_user)
        TransferUserService.transfer_links_set(old_user, new_user)
        TransferUserService.transfer_transaction(old_user, new_user)
        TransferUserService.transfer_payments(old_user, new_user)
        TransferUserService.transfer_user_domains(old_user, new_user)
        TransferUserService.transfer_tlg_acc_data(old_user, new_user)

        return True

    @staticmethod
    def transfer_links(old_user, new_user):
        """
        Перенос ссылок между аккаунтами
        """
        links = Links.objects.filter(tlg_id=old_user)
        links.update(tlg_id=new_user)

    @staticmethod
    def transfer_links_set(old_user, new_user):
        """
        Перенос набора ссылок между аккаунтами
        """
        linksets = LinkSet.objects.filter(tlg_id=old_user)
        linksets.update(tlg_id=new_user)

    @staticmethod
    def transfer_transaction(old_user, new_user):
        """
        Перенос транзакций между аккаунтами
        """
        transactions = Transaction.objects.filter(user=old_user)
        transactions.update(user=new_user)

    @staticmethod
    def transfer_payments(old_user, new_user):
        """
        Перенос платежей между аккаунтами
        """
        payments = Payments.objects.filter(tlg_id=old_user)
        payments.update(tlg_id=new_user)

    @staticmethod
    def transfer_user_domains(old_user, new_user):
        """
        Перенос личных доменов пользоателей между аккаунтами
        """
        user_domains = UserDomains.objects.filter(tlg_user=old_user)
        user_domains.update(tlg_user=new_user)


    @staticmethod
    def transfer_tlg_acc_data(old_user, new_user):
        """
        Перенос данных в боте (баланс и т.д.) между аккаунтами
        """
        new_user.balance = old_user.balance
        new_user.interface_language = old_user.interface_language
        new_user.save()
