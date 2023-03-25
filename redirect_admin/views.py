from loguru import logger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from redirect_admin.models import TlgUser, RedirectBotSettings, Links
from redirect_admin.serializers import TlgUserSerializer, RedirectBotSettingsSerializer, LinksSerializer


class TlgUserView(APIView):
    """
    Вьюшка для обработки запросов, связанных с моделью TlgUser.
    """
    def get(self, request, format=None):
        """
                Обработка GET запроса:
                    ?tlg_id=.. - получение данных об одном пользователе по tlg_id
                """
        tlg_id = request.query_params.get('tlg_id')
        if tlg_id and str(tlg_id).isdigit():

            try:
                tlg_user_obj = TlgUser.objects.get(tlg_id=tlg_id)
            except Exception as error:
                logger.error(f"Не удалось получить объект TlgUser, запрошен по tlg_id={tlg_id}\nТекст ошибки: {error}")
                return Response(status=status.HTTP_400_BAD_REQUEST)

            bot_user_serializer = TlgUserSerializer(tlg_user_obj, many=False).data
            logger.success(f'REDIRECT_BOT | Успешно обработан GET запрос на получение объекта TlgUser')
            return Response(bot_user_serializer, status.HTTP_200_OK)

        else:
            logger.warning(f'REDIRECT_BOT | Неверные параметры запроса для получения объекта TlgUser')
            return Response({'result': 'Неверные параметры запроса'}, status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        """
        Обработка POST запроса.
        """
        logger.info(f'Получен запрос от REDIRECT_BOT на запись пользователя.')
        serializer = TlgUserSerializer(data=request.data)
        if serializer.is_valid():
            tlg_user_obj = TlgUser.objects.update_or_create(
                tlg_id=serializer.data.get('tlg_id'),
                defaults=serializer.data
            )
            logger.success(f'Пользователь REDIRECT_BOT c TG_ID == {serializer.data.get("tlg_id")} '
                           f'был {"создан" if tlg_user_obj[1] else "обновлён"}.')
            result_object = TlgUserSerializer(tlg_user_obj[0], many=False).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            logger.warning(f'Данные от REDIRECT_BOT на запись пользователя не прошли валидацию.')
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


class GetSettingsView(APIView):
    """
    Вьюшка для обработки запросов, связанных с получением ключей из таблицы RedirectBotSettings.
    """
    def get(self, request, format=None):
        """
        Обработка GET запроса для получения данных по ключу
        ?key - ключ настройки
        """
        redirect_bot_settings_obj = RedirectBotSettings.objects.filter(key=request.GET.get('key'))
        redirect_bot_settings_serializer = RedirectBotSettingsSerializer(redirect_bot_settings_obj, many=True).data
        return Response(redirect_bot_settings_serializer, status.HTTP_200_OK)


class LinksView(APIView):
    """
    Вьюшка для обработки запросов создания и получения данных модели Links.
    """
    def post(self, request, format=None):
        """
        Обработка POST запроса. Создаём запись в таблице Links.
        """
        logger.info(f'Получен запрос от REDIRECT_BOT на создание/обновление ссылки.')
        serializer = LinksSerializer(data=request.data)
        if serializer.is_valid() and str(request.data.get('tlg_id')).isdigit():
            tlg_user = TlgUser.objects.get(tlg_id=request.data.get('tlg_id'))
            link_obj = Links.objects.update_or_create(
                id=serializer.data.get('link_id'),
                defaults={
                    'tlg_user': tlg_user,
                    'link': serializer.data.get('link'),
                }
            )
            logger.success(f'REDIRECT_BOT | Ссылка {serializer.data.get("link")}'
                           f' для юзера TG_ID == {request.data.get("tlg_id")} '
                           f'была {"создана" if link_obj[1] else "обновлёна"}.')
            result_object = LinksSerializer(link_obj[0], many=False).data
            return Response({f"Link {'created' if link_obj[1] else 'updated'}": result_object}, status.HTTP_200_OK)
        else:
            logger.warning(f'Данные от REDIRECT_BOT на запись/обновление ссылки не валидны.\nЗапрос: {request.data}')
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)
