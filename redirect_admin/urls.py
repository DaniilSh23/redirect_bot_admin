from django.urls import path

from redirect_admin.views import TlgUserView, GetSettingsView, LinksView

app_name = 'redirect_admin'

urlpatterns = [
    path('tlg_user/', TlgUserView.as_view(), name='tlg_user'),
    path('get_settings/', GetSettingsView.as_view(), name='get_settings'),
    path('links/', LinksView.as_view(), name='links')
]
