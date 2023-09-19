from django.contrib import admin

from redirect_admin.admin_mixins import ExportUsernames
from redirect_admin.models import TlgUser, RedirectBotSettings, Links, LinkSet, Payments, Transaction


@admin.register(TlgUser)
class TlgUserAdmin(admin.ModelAdmin, ExportUsernames):
    """
    Регистрация модели TlgUser в админке.
    """
    actions = [
        'export_usernames',
    ]
    list_display = (
        "id",
        "tlg_id",
        "first_name",
        "username",
        "is_verified",
        "is_scam",
        "is_fake",
    )
    list_display_links = (
        "id",
        "tlg_id",
        "first_name",
        "username",
    )
    search_fields = "tlg_id", "first_name", "username"
    search_help_text = "Поиск по TG ID, TG имени, TG username"
    ordering = ['-id']
    fieldsets = [
        ('Основная информация', {
            "fields": ("tlg_id", "username", "first_name", "last_name"),
            "classes": ("wide", "extrapretty"),
            "description": "Основные данные о пользвателе Telegram.",
        }),
        ('Финансы', {
            'fields': ('balance',),
            'classes': ('wide', 'extrapretty', 'collapse'),
            'description': 'Данные, связанные с деньгами: баланс, ID счетов и т.п.'
        }),
        ('Дополнительная информация', {
            'fields': ('is_verified', 'is_scam', 'is_fake', 'is_premium', 'language_code'),
            'classes': ('wide', 'collapse'),
            'description': 'Дополнительная информация о пользователе Telegram, '
                           'такая как: верификация, мошенничество и т.д.',
        })
    ]


@admin.register(Links)
class LinksAdmin(admin.ModelAdmin):
    """
    Регистрация в админке модели для настроек Links.
    """
    list_display = (
        "id",
        'tlg_id',
        'link',
        'redirect_links',
        'short_links',
        'redirect_numb',
        'company_id',
        'created_at',
    )
    list_display_links = (
        "id",
        'tlg_id',
        'link',
        'redirect_links',
        'short_links'
        'redirect_numb',
        'company_id',
        'created_at',
    )
    search_fields = (
        'tlg_id__tlg_id',  # Пример: поиск по имени автора
        'link',
        'redirect_links',
        'short_links',
        'redirect_numb',
        'company_id',
    )
    search_help_text = ('поиск по полям: Автор (по TG ID), Ссылка, Редирект ссылки, '
                        'Сокращённые ссылки, Кол-во редиректов, ID компании(keitaro)')

    fieldsets = [
        ('Основная информация', {
            'fields': ('tlg_id', 'link_set', 'link', 'redirect_numb'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Основная информация о ссылке. Это то, что даёт нам на вход юзер.'
        }),
        ('Обработка KEITARO', {
            'fields': ('company_id', 'redirect_links'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Информация, которую получаем после обработки KEITARO. '
                           'В поле "Редирект ссылки" ссылки должны быть указаны через пробел'
        }),
        ('Сервисы сокращения', {
            'fields': ('short_link_service', 'short_links'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Информация, которую получаем после обработки сервисом сокращения ссылок. '
                           'В поле "Сокращённые ссылки" ссылки должны быть указаны через пробел'
        })
    ]


@admin.register(LinkSet)
class LinkSetAdmin(admin.ModelAdmin):
    """
    Регистрация в админке модели LinkSet
    """
    list_display = (
        "id",
        'tlg_id',
        'title',
        'created_at',
    )
    list_display_links = (
        "id",
        'tlg_id',
        'title',
        'created_at',
    )


@admin.register(RedirectBotSettings)
class RedirectBotSettingsAdmin(admin.ModelAdmin):
    """
    Регистрация в админке модели для настроек RedirectBotSettings.
    """
    list_display = ('key', 'value')
    list_display_links = ('key', 'value')


@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    """
    Регистрация в админке модели Payments.
    """
    list_display = (
        "id",
        'tlg_id',
        'pay_system_type',
        'amount',
        'bill_expire_at',
        'bill_status',
        'created_at',
        'archived',
    )
    list_display_links = (
        "id",
        'tlg_id',
        'pay_system_type',
        'amount',
        'bill_expire_at',
        'bill_status',
        'created_at',
        'archived',
    )
    search_fields = (
        'tlg_id',
        'pay_system_type',
        'amount',
        'bill_expire_at',
        'bill_status',
        'created_at',
    )
    search_help_text = 'Поиск по всем полям таблицы'
    list_filter = (
        'tlg_id',
        'pay_system_type',
        'bill_status',
        'archived',
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'transaction_type',
        'transaction_datetime',
        'amount',
        'description',
    )
    list_display_links = (
        'user',
        'transaction_type',
        'transaction_datetime',
        'amount',
        'description',
    )
    search_fields = (
        'user',
        'transaction_type',
        'transaction_datetime',
        'amount',
        'description',
    )
    search_help_text = 'Поиск по всем полям таблицы'
    list_filter = (
        'transaction_type',
    )
