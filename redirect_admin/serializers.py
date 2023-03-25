from rest_framework import serializers

from redirect_admin.models import TlgUser, RedirectBotSettings, Links


class TlgUserSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели TlgUser
    """
    class Meta:
        model = TlgUser
        fields = '__all__'


class RedirectBotSettingsSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели RedirectBotSettings.
    """
    class Meta:
        model = RedirectBotSettings
        fields = '__all__'


class LinksSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели Links.
    """
    class Meta:
        model = Links
        fields = ('link',)
