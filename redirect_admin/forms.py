from django import forms
from django.core.validators import RegexValidator


class UserDomainForm(forms.Form):
    """
    Форма с данными для создания домена пользователя
    """
    domain = forms.URLField()
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])
