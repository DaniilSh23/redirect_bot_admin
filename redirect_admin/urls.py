from django.urls import path

from redirect_admin.views import UserDomainView, TlgUserView, GetSettingsView, LinksView, LinkSetView, StartLinkWrapping, \
    PaymentsView, ChangeBalance, GetLinkOwner, TransactionView, get_up_bot, InterfaceLanguage, UserDomainDeleteView

app_name = 'redirect_admin'

urlpatterns = [
    # Общее
    path('get_settings/', GetSettingsView.as_view(), name='get_settings'),

    # Для редиректа (основной функционал)
    path('links/', LinksView.as_view(), name='links'),
    path('link_set/', LinkSetView.as_view(), name='link_set'),
    path('get_link_owner/', GetLinkOwner.as_view(), name='get_link_owner'),
    path('start_wrapping/', StartLinkWrapping.as_view(), name='start_wrapping'),
    path('user_domain_delete/<int:pk>', UserDomainDeleteView.as_view(), name='user_domain_delete'),
    path('user_domain/', UserDomainView.as_view(), name='user_domain'),

    # Пользовательские
    path('tlg_user/', TlgUserView.as_view(), name='tlg_user'),
    path('interface_lang/', InterfaceLanguage.as_view(), name='interface_lang'),

    # Бабки
    path('payments/', PaymentsView.as_view(), name='payments'),
    path('change_balance/', ChangeBalance.as_view(), name='change_balance'),
    path('transaction/', TransactionView.as_view(), name='transaction'),

    # Управление ботом
    path('get_up_bot/', get_up_bot, name='get_up_bot'),
]
