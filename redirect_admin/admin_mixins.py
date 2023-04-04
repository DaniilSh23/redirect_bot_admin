from django.http import HttpRequest, HttpResponse
from django.db.models import QuerySet
from django.db.models.options import Options


class ExportUsernames:
    """
    Миксин для админки. Экспорт Telegram usernames в текстовый файл при их наличии у юзеров.
    """
    def export_usernames(self, request: HttpRequest, queryset: QuerySet):
        """
        Метод для экспорта юзернеймов в текстовый файл
        """
        meta: Options = self.model._meta
        field_names = [i_field.name for i_field in meta.fields]     # Сложим название полей модели в список

        # Подготовим объект ответа на запрос
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename=tlg_usernames--export.txt'

        # Записываем юзернеймы в ответ, как будто в файл
        for i_obj in queryset:
            if i_obj.username:
                response.write(f"{i_obj.username}\n")

        return response

    export_usernames.short_description = 'Экспорт в файл TG Usernames'
