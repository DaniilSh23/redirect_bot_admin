"""
Реализации паттерна сага для выполнения тех или иных действий.
"""


from redirect_admin.services import RedirectBotSettingsService, UserDomainService
from redirect_admin.claudflare import ClaudFlareAgent
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
        
        # Получаем необходимые данные для работы с ClaudFlare
        ip_for_a_record = RedirectBotSettingsService.read(key="keitaro_main_domain")
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
            UserDomainService.delete(record=self.user_domain_obj)
            return False
        
        # Устанавливаем DNS запись для новой зоны (домена)
        if not claud_agent.set_dns_for_new_zone(ip_for_a_record=ip_for_a_record):
            MY_LOGGER.error(self.err_msg)
            UserDomainService.delete(record=self.user_domain_obj)
            return False
        
        return True