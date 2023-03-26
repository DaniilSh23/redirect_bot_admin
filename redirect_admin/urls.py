from django.urls import path

from redirect_admin.views import TlgUserView, GetSettingsView, LinksView, LinkSetView, StartLinkWrapping

app_name = 'redirect_admin'

urlpatterns = [
    path('tlg_user/', TlgUserView.as_view(), name='tlg_user'),
    path('get_settings/', GetSettingsView.as_view(), name='get_settings'),
    path('links/', LinksView.as_view(), name='links'),
    path('link_set/', LinkSetView.as_view(), name='link_set'),
    path('start_wrapping/', StartLinkWrapping.as_view(), name='start_wrapping'),
]
