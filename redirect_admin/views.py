from loguru import logger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from redirect_admin.models import TlgUser, RedirectBotSettings, Links, LinkSet
from redirect_admin.serializers import TlgUserSerializer, RedirectBotSettingsSerializer, LinksSerializer, \
    LinkSetSerializer


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
        Параметры запроса:
            id - ID ранее созданной записи (int)
            tlg_id - TG ID юзера, до 25 символов (int)
            link - название набора ссылок, до 1000 символов (str, URLField)
            link_set_id - ID набора ссылок (int)
            redirect_numb - кол-во редиректов (int)
        """
        logger.info(f'Получен запрос от REDIRECT_BOT на создание/обновление ссылки.')
        serializer = LinksSerializer(data=request.data, many=True)
        if serializer.is_valid():

            rslt_objects = []
            for i_link in serializer.data:
                tlg_user = TlgUser.objects.get(tlg_id=i_link.get('tlg_id'))
                link_set_obj = LinkSet.objects.get(id=i_link.get('link_set_id'))
                link_obj = Links.objects.update_or_create(
                    id=i_link.get('id'),
                    defaults={
                        'tlg_id': tlg_user,
                        'link': i_link.get('link'),
                        'link_set': link_set_obj,
                        'redirect_numb': i_link.get('redirect_numb'),
                    }
                )
                logger.success(f'REDIRECT_BOT | Ссылка {i_link.get("link")}'
                               f' для юзера TG_ID == {i_link.get("tlg_id")} '
                               f'была {"создана" if link_obj[1] else "обновлёна"} {link_obj[0].id}.')
                rslt_objects.append(link_obj[0])

            result_object = LinksSerializer(rslt_objects, many=True).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            logger.warning(f'Данные от REDIRECT_BOT на запись/обновление ссылки не валидны.\nЗапрос: {request.data}')
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


class LinkSetView(APIView):
    """
    Вьюшка для работы с записями модели LinkSet.
    """
    def post(self, request, format=None):
        """
        Создание | обновление записи в модели LinkSet.
        Параметры запроса:
            id - id ранее созданной записи в БД (int) (может быть None(null))
            tlg_id - tlg id юзера, до 25 символов (str)
            title - название набора ссылок, до 200 символов (str)
        """
        logger.info(f'Получен запрос от REDIRECT_BOT на создание/обновление набора ссылок.')
        serializer = LinkSetSerializer(data=request.data, many=False)
        if serializer.is_valid():
            tlg_user = TlgUser.objects.get(tlg_id=request.data.get('tlg_id'))
            link_set_obj = LinkSet.objects.update_or_create(
                id=serializer.data.get('id'),
                defaults={
                    "tlg_id": tlg_user,
                    "title": serializer.data.get("title"),
                }
            )
            logger.success(f"Успешное {'создание' if link_set_obj[1] else 'обновление'} набора ссылок.")
            serialized_obj = LinkSetSerializer(instance=link_set_obj[0], many=False).data
            return Response(serialized_obj, status.HTTP_200_OK)

        else:
            logger.warning(f'Данные от REDIRECT_BOT на создание/обновление набора ссылок не валидны.\n'
                           f'Запрос: {request.data}')
            return Response({'result': 'Переданные данные не прошли валидацию.'}, status.HTTP_400_BAD_REQUEST)


class StartLinkWrapping(APIView):
    """
    Вьюшка для старта обёртки ссылок. Принимает ID набора ссылок.
    """
    def post(self, request, format=None):
        """
        POST запрос.
            link_set_id - ID набора ссылок
        """
        from redirect_admin.tasks import wrap_links_in_redirect

        logger.info(f'Получен запрос от REDIRECT_BOT для старта обёртки ссылок.')
        if str(request.data.get('link_set_id')).isdigit():
            wrap_links_in_redirect.delay(link_set_id=request.data.get('link_set_id'))
            logger.info(f'Запущена отложенная задача для обёртки ссылок '
                        f'из набора с ID == {request.data.get("link_set_id")}')
            return Response(status.HTTP_200_OK)
        else:
            logger.warning(f'Данные от REDIRECT_BOT для старта обёртки ссылок не валидны.\n'
                           f'Запрос: {request.data}')
            return Response({'result': 'Переданные данные не прошли валидацию.'}, status.HTTP_400_BAD_REQUEST)
