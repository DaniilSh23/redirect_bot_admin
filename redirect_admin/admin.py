from django.contrib import admin

from redirect_admin.models import TlgUser, RedirectBotSettings, Links, LinkSet


@admin.register(TlgUser)
class TlgUserAdmin(admin.ModelAdmin):
    """
    Регистрация модели TlgUser в админке.
    """
    actions = [
        'export_csv_for_dyatel_project',
    ]
    list_display = (
        "tlg_id",
        "first_name",
        "username",
        "is_verified",
        "is_scam",
        "is_fake",
    )
    list_display_links = (
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
        'tlg_id',
        'link',
        'redirect_numb',
        'company_id',
        'created_at',
    )
    list_display_links = (
        'tlg_id',
        'link',
        'redirect_numb',
        'company_id',
        'created_at',

    )
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
        'tlg_id',
        'title',
        'created_at',
    )
    list_display_links = (
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
