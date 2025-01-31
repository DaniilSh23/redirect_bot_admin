from django import forms
from django.core.validators import RegexValidator


class BaseTlgIdForm(forms.Form):
    """
    Базовая форма с tlg_id.
    """
    tlg_id = forms.CharField(validators=[RegexValidator(
        regex=r'^\d+$',  # Регулярное выражение для цифр
        message='запрос не из телеграмма',
        code='invalid_tlg_id'
    )])

class UserDomainForm(BaseTlgIdForm):
    """
    Форма с данными для создания домена пользователя
    """
    domain = forms.CharField(
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$",
                message="неверный домен, пример: example.com",
                code="invalid_domain_name",
            )
        ]
    )

