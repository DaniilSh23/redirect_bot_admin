from django.db import models


class RedirectBotSettings(models.Model):
    """
    Настройки для Redirect Bot.
    """

    key = models.CharField(verbose_name="Ключ", max_length=230)
    value = models.TextField(verbose_name="Значение", max_length=500)

    class Meta:
        ordering = ["-id"]
        verbose_name = "настройка Redirect Bot"
        verbose_name_plural = "настройки Redirect Bot"


class TlgUser(models.Model):
    """
    Модель пользователя телеграм.
    """

    tlg_id = models.CharField(verbose_name="TG ID", max_length=30)
    is_verified = models.BooleanField(
        verbose_name="Telegram его проверил", default=False
    )
    is_scam = models.BooleanField(verbose_name="Мошенник", default=False)
    is_fake = models.BooleanField(verbose_name="Выдаёт себя за другого", default=False)
    is_premium = models.BooleanField(verbose_name="Премиум", default=False)
    first_name = models.CharField(
        verbose_name="Имя(TG)", max_length=100, blank=True, null=False
    )
    last_name = models.CharField(
        verbose_name="Фамилия(TG)", max_length=100, blank=True, null=False
    )
    username = models.CharField(
        verbose_name="username(TG)", max_length=100, blank=True, null=False
    )
    language_code = models.CharField(
        verbose_name="языковой код(TG)", max_length=20, blank=True, null=False
    )
    balance = models.DecimalField(
        verbose_name="Баланс", max_digits=10, decimal_places=2, default=0
    )
    interface_language = models.ForeignKey(
        verbose_name="язык интерфейса",
        to="InterfaceLanguages",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Пользователь с TG ID: {self.tlg_id}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "пользователь TG"
        verbose_name_plural = "пользователи TG"


class UserDomains(models.Model):
    """
    Модель с собственными доменами пользователей.
    """

    tlg_user = models.ForeignKey(
        verbose_name="Автор", to=TlgUser, on_delete=models.CASCADE
    )
    domain = models.URLField(verbose_name="Домен", max_length=200)
    keitaro_id = models.CharField(verbose_name="ID в KEITARO", blank=True, default="", max_length=6)
    claudflare_id = models.CharField(verbose_name="ID в ClaudFlare", blank=True, default="", max_length=50)
    claudflare_zone_dns_id = models.CharField(verbose_name="ID DNS в ClaudFlare", blank=True, default="", max_length=50)
    created_at = models.DateTimeField(
        verbose_name="Дата и время создания", auto_now_add=True
    )

    def __str__(self):
        return f"User domain: {self.domain}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Домен пользователя"
        verbose_name_plural = "Домены пользователей"


class InterfaceLanguages(models.Model):
    """
    Модель для хранения доступных языков интерфейса бота.
    """

    language_code = models.CharField(verbose_name="языковой код", max_length=5)
    language = models.CharField(verbose_name="язык", max_length=25)
    default_language = models.BooleanField(verbose_name="дефолтный язык", default=False)

    def __str__(self):
        return f"язык интерфейса: {self.language_code}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "язык интерфейса"
        verbose_name_plural = "языки интерфейса"


class LinkSet(models.Model):
    """
    Таблицы для наборов ссылок. Нужна, чтобы сгруппировать ссылки.
    """

    tlg_id = models.ForeignKey(
        verbose_name="Автор", to=TlgUser, on_delete=models.CASCADE
    )
    title = models.CharField(verbose_name="Название набора", max_length=200)
    created_at = models.DateTimeField(
        verbose_name="Дата и время создания", auto_now_add=True
    )

    def __str__(self):
        return f"Набор ссылок: {self.title}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Набор ссылок"
        verbose_name_plural = "Наборы ссылок"


class Links(models.Model):
    """
    Таблица со ссылками TLG юзеров.
    """

    SHORT_LINKS_SRVCS = (
        ("cutt.ly", "cutt.ly"),
        ("cutt.us", "cutt.us"),
        ("clck.ru", "clck.ru"),
        ("kortlink.dk", "kortlink.dk"),
        ("gg.gg", "gg.gg"),
        ("t9y.me", "t9y.me"),
        ("custom_domain", "custom_domain"),
        ("user_domain", "user_domain"),
    )

    tlg_id = models.ForeignKey(
        verbose_name="Автор", to=TlgUser, on_delete=models.CASCADE
    )
    link_set = models.ForeignKey(
        verbose_name="Набор ссылок", to=LinkSet, on_delete=models.CASCADE
    )
    link = models.URLField(verbose_name="Ссылка", max_length=1000)
    redirect_numb = models.IntegerField(verbose_name="Кол-во редиректов")
    company_id = models.CharField(
        verbose_name="ID компании(keitaro)", max_length=150, blank=True, null=True
    )
    redirect_links = models.TextField(
        verbose_name="Редирект ссылки", max_length=25000, blank=True, null=True
    )
    short_link_service = models.CharField(
        verbose_name="Сервис сокращения ссылок",
        choices=SHORT_LINKS_SRVCS,
        max_length=14,
        blank=True,
        null=True,
    )
    short_links = models.TextField(
        verbose_name="Сокращённые ссылки", max_length=25000, blank=True, null=True
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    def __str__(self):
        return f"Ссылка: {self.link}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Ссылка"
        verbose_name_plural = "Ссылки"


class Payments(models.Model):
    """
    Модель для платежей.
    """

    PAY_SYSTEMS_LST = (
        ("qiwi", "QIWI"),
        ("crystal", "Crystal Pay"),
        ("to_card", "Перевод на карту"),
    )
    tlg_id = models.ForeignKey(
        verbose_name="Чей платёж", to=TlgUser, on_delete=models.CASCADE
    )
    pay_system_type = models.CharField(
        verbose_name="Платёжная сис-ма", choices=PAY_SYSTEMS_LST, max_length=7
    )
    amount = models.DecimalField(
        verbose_name="Сумма платежа(руб.)", max_digits=10, decimal_places=2
    )
    bill_id = models.CharField(verbose_name="ID счёта на оплату", max_length=350)
    bill_url = models.URLField(verbose_name="Ссылка счёта", max_length=500)
    bill_status = models.BooleanField(verbose_name="Счёт оплачен", default=False)
    bill_expire_at = models.DateTimeField(
        verbose_name="Дата аннулирования счёта на оплату"
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    archived = models.BooleanField(verbose_name="В архиве", default=False)

    def __str__(self):
        return f"Счёт: {self.bill_id}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Счёт"
        verbose_name_plural = "Счета"


class Transaction(models.Model):
    """
    Транзакции.
    """

    TRANSACTION_TYPE_LST = [
        ("replenishment", "пополнение"),
        ("write-off", "списание"),
    ]
    user = models.ForeignKey(
        verbose_name="Пользователь", to=TlgUser, on_delete=models.CASCADE
    )
    transaction_type = models.CharField(
        verbose_name="Тип транзакции", choices=TRANSACTION_TYPE_LST, max_length=13
    )
    transaction_datetime = models.DateTimeField(
        verbose_name="Дата и время транзакции", auto_now_add=True
    )
    amount = models.DecimalField(
        verbose_name="Сумма", default=0, max_digits=10, decimal_places=2
    )
    description = models.TextField(verbose_name="Описание", max_length=1000, null=True)

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ["-id"]
