from abc import ABC

from rest_framework import serializers

from redirect_admin.models import TlgUser, RedirectBotSettings, Links, LinkSet


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


class LinksSerializer(serializers.Serializer):
    """
    Сериалайзер для модели Links.
    """
    id = serializers.IntegerField(allow_null=True)
    tlg_id = serializers.CharField(max_length=25)
    link = serializers.URLField(max_length=1000)
    link_set_id = serializers.IntegerField()
    redirect_numb = serializers.IntegerField()


class LinkSetSerializer(serializers.Serializer):
    """
    Сериалайзер для модели LinkSet.
    """
    id = serializers.IntegerField(allow_null=True)
    tlg_id = serializers.CharField(max_length=25)
    title = serializers.CharField(max_length=200)
