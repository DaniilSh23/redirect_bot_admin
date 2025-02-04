"""
Реализации паттерна сага для выполнения тех или иных действий.
"""


from redirect_admin.services import RedirectBotSettingsService, UserDomainService
from redirect_admin.claudflare import ClaudFlareAgent
from redirect_admin.keitaro import KeitaroAgent
from redirect_bot_admin.settings import MY_LOGGER


class AddUserDomainSaga:
    """
    Сага для создания домена пользователя.
    """
    err_msg = "Ошибка при выполнении саги создания домена пользователя"

    def __init__(self, user_tlg_id: int, domain: str):
        """
        Конструктор для класса саги.
        """
        self.user_tlg_id = user_tlg_id
        self.domain = domain

    def create_user_domain(self) -> bool:
        """
        Создание домена пользователя. Возвращает флаг успешности выполнения саги.
        """


        # Создаем в БД запись с новым доменом юзера
        self.user_domain_obj = UserDomainService.create(user_tlg_id=self.user_tlg_id, domain=self.domain)
        if not self.user_domain_obj:
            MY_LOGGER.error(self.err_msg)
            return False
        
        # Создаем новый домен в Keitaro
        keitaro_agent = KeitaroAgent()
        keitaro_domain_id = keitaro_agent.create_domain(domain=self.domain)
        if not keitaro_domain_id:
            MY_LOGGER.error(self.err_msg)
            UserDomainService.delete(record=self.user_domain_obj)
            return False
        self.user_domain_obj.keitaro_id = keitaro_domain_id
        self.user_domain_obj.save()
        
        # Получаем необходимые данные для работы с ClaudFlare
        ip_for_a_record = keitaro_agent.keitaro_address
        claudflare_email = RedirectBotSettingsService.read(key="claudflare_email")
        claudlare_api_key = RedirectBotSettingsService.read(key="claudlare_api_key")
        if not ip_for_a_record or not claudflare_email or not claudlare_api_key:
            MY_LOGGER.error(self.err_msg)
            UserDomainService.delete(record=self.user_domain_obj)
            return False
        
        # Создаем объект зоны (домена) в ClaudFlare
        claud_agent = ClaudFlareAgent(claudflare_email=claudflare_email, claudlare_api_key=claudlare_api_key, domain=self.domain)
        if not claud_agent.create_zone():
            MY_LOGGER.error(self.err_msg)
            keitaro_agent.delete_domain(domain_keitaro_id=self.user_domain_obj.keitaro_id)
            UserDomainService.delete(record=self.user_domain_obj)
            return False
        self.user_domain_obj.claudflare_id = claud_agent.new_zone_id
        self.user_domain_obj.save()
        
        # Устанавливаем DNS запись для новой зоны (домена)
        if not claud_agent.set_dns_for_new_zone(ip_for_a_record=ip_for_a_record):
            MY_LOGGER.error(self.err_msg)
            keitaro_agent.delete_domain(domain_keitaro_id=self.user_domain_obj.keitaro_id)
            UserDomainService.delete(record=self.user_domain_obj)
            return False
        self.user_domain_obj.claudflare_zone_dns_id = claud_agent.new_zone_dns_record_id
        self.user_domain_obj.save()
        
        return True


class DeleteUserDomainSaga:
    """
    Сага для удаления домена пользователя.
    """
    err_msg = "Ошибка при выполнении саги удаления домена пользователя"
    
    def __init__(self, user_tlg_id: int, domain_pk: int):
        """
        Конструктор для класса саги.
        """
        self.user_tlg_id = user_tlg_id
        self.domain_pk = domain_pk

    def delete_user_domain(self) -> bool:
        """
        Сага для удаления домена юзера
        """
        # Получение объекта домена и иных данных
        user_domain = UserDomainService.read(pk=self.domain_pk)
        claudflare_email = RedirectBotSettingsService.read(key="claudflare_email")
        claudlare_api_key = RedirectBotSettingsService.read(key="claudlare_api_key")
        if not user_domain or not claudflare_email or not claudlare_api_key:
            MY_LOGGER.warning(self.err_msg)
            return False

        # Удаление домена в кейтаро
        keitaro_agent = KeitaroAgent()
        res = keitaro_agent.delete_domain(domain_keitaro_id=user_domain.keitaro_id)     # Удаление домена в архив
        if not res:
            MY_LOGGER.warning(self.err_msg)
            return False

        # Удаление DNS записи домена (zone) из ClaudFlare
        claud_agent = ClaudFlareAgent(claudflare_email=claudflare_email, claudlare_api_key=claudlare_api_key)
        claud_agent.delete_zone_dns_record(domain_id=user_domain.claudflare_id, dns_record_id=user_domain.claudflare_zone_dns_id)
        if not res:
            MY_LOGGER.warning(self.err_msg)
            return False

        # Удаление домена (zone) из ClaudFlare
        res = claud_agent.delete_zone(domain_id=user_domain.claudflare_id)
        if not res:
            MY_LOGGER.warning(self.err_msg)
            return False
        
        # Удаление из БД
        UserDomainService.delete(record=user_domain)
        return True