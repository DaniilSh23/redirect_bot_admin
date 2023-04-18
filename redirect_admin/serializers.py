from rest_framework import serializers

from redirect_admin.models import TlgUser, RedirectBotSettings, Payments, Links


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
    short_link_service = serializers.CharField(max_length=15)


class LinksModelSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели Links. Нужен, чтобы без гемора отдавать на GET запрос.
    """
    class Meta:
        model = Links
        fields = '__all__'


class LinkSetSerializer(serializers.Serializer):
    """
    Сериалайзер для модели LinkSet.
    """
    id = serializers.IntegerField(allow_null=True)
    tlg_id = serializers.CharField(max_length=25)
    title = serializers.CharField(max_length=200)


class PaymentsSerializer(serializers.Serializer):
    """
    Сериалайзер для модели Payments
    """
    tlg_id = serializers.CharField(max_length=25)
    pay_system_type = serializers.CharField(max_length=7)
    amount = serializers.CharField(max_length=15)
    bill_id = serializers.CharField(max_length=350)
    bill_status = serializers.BooleanField(default=False)
    bill_expire_at = serializers.DateTimeField()
    bill_url = serializers.URLField(max_length=500)


class PaymentsModelSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для модели Payments (нужен, когда отдаём запись по GET запросу)
    """
    class Meta:
        model = Payments
        fields = '__all__'
