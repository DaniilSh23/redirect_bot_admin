from django.db import models


class TlgUser(models.Model):
    """
    Модель пользователя телеграм.
    """
    tlg_id = models.CharField(verbose_name='TG ID', max_length=30)
    is_verified = models.BooleanField(verbose_name='Telegram его проверил', default=False)
    is_scam = models.BooleanField(verbose_name='Мошенник', default=False)
    is_fake = models.BooleanField(verbose_name='Выдаёт себя за другого', default=False)
    is_premium = models.BooleanField(verbose_name='Премиум', default=False)
    first_name = models.CharField(verbose_name='Имя(TG)', max_length=100, blank=True, null=False)
    last_name = models.CharField(verbose_name='Фамилия(TG)', max_length=100, blank=True, null=False)
    username = models.CharField(verbose_name='username(TG)', max_length=100, blank=True, null=False)
    language_code = models.CharField(verbose_name='языковой код(TG)', max_length=20, blank=True, null=False)
    balance = models.DecimalField(verbose_name='Баланс', max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Пользователь с TG ID: {self.tlg_id}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'пользователь TG'
        verbose_name_plural = 'пользователи TG'


class LinkSet(models.Model):
    """
    Таблицы для наборов ссылок. Нужна, чтобы сгруппировать ссылки.
    """
    tlg_id = models.ForeignKey(verbose_name='Автор', to=TlgUser, on_delete=models.CASCADE)
    title = models.CharField(verbose_name='Название набора', max_length=200)
    created_at = models.DateTimeField(verbose_name='Дата и время создания', auto_now_add=True)

    def __str__(self):
        return f'Набор ссылок: {self.title}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Набор ссылок'
        verbose_name_plural = 'Наборы ссылок'


class Links(models.Model):
    """
    Таблица со ссылками TLG юзеров.
    """
    SHORT_LINKS_SRVCS = (
        ('cutt.ly', 'cutt.ly'),
        ('cutt.us', 'cutt.us'),
        ('clck.ru', 'clck.ru'),
        ('kortlink.dk', 'kortlink.dk'),
        ('gg.gg', 'gg.gg'),
        ('t9y.me', 't9y.me'),
    )

    tlg_id = models.ForeignKey(verbose_name='Автор', to=TlgUser, on_delete=models.CASCADE)
    link_set = models.ForeignKey(verbose_name='Набор ссылок', to=LinkSet, on_delete=models.CASCADE)
    link = models.URLField(verbose_name='Ссылка', max_length=1000)
    redirect_numb = models.IntegerField(verbose_name='Кол-во редиректов')
    company_id = models.CharField(verbose_name='ID компании(keitaro)', max_length=150, blank=True, null=True)
    redirect_links = models.TextField(verbose_name='Редирект ссылки', max_length=25000, blank=True, null=True)
    short_link_service = models.CharField(verbose_name='Сервис сокращения ссылок', choices=SHORT_LINKS_SRVCS,
                                          max_length=11, blank=True, null=True)
    short_links = models.TextField(verbose_name='Сокращённые ссылки', max_length=25000, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)

    def __str__(self):
        return f'Ссылка: {self.link}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'


class RedirectBotSettings(models.Model):
    """
    Настройки для Redirect Bot.
    """
    key = models.CharField(verbose_name='Ключ', max_length=230)
    value = models.TextField(verbose_name='Значение', max_length=500)

    class Meta:
        ordering = ['-id']
        verbose_name = 'настройка Redirect Bot'
        verbose_name_plural = 'настройки Redirect Bot'
