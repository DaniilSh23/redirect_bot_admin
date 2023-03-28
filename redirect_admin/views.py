import datetime

import pytz
from loguru import logger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from redirect_admin.models import TlgUser, RedirectBotSettings, Links, LinkSet, Payments
from redirect_admin.serializers import TlgUserSerializer, RedirectBotSettingsSerializer, LinksSerializer, \
    LinkSetSerializer, PaymentsSerializer, PaymentsModelSerializer


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
            tlg_user_obj = TlgUser.objects.get_or_create(
                tlg_id=serializer.data.get('tlg_id'),
                defaults=serializer.data
            )
            logger.success(f'Пользователь REDIRECT_BOT c TG_ID == {serializer.data.get("tlg_id")} '
                           f'{"был создан" if tlg_user_obj[1] else "уже есть в БД"}.')
            result_object = TlgUserSerializer(tlg_user_obj[0], many=False).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            logger.warning(f'Данные от REDIRECT_BOT на запись пользователя не прошли валидацию.')
            return Response({'result': 'Переданные данные не прошли валидацию'}, status.HTTP_400_BAD_REQUEST)


class ChangeBalance(APIView):
    """
    Вьюха для изменения баланса.
    """
    def post(self, request, format=None):
        logger.info(f'Получен запрос от редирект бота на изменение баланса юзера TG ID == {request.data.get("tlg_id")}'
                    f' на {request.data.get("action")}{request.data.get("value")} руб.')

        # Проверка данных, которые пришли в запросе
        if (request.data.get("action") == '+' or request.data.get("action") == '-') and \
                str(request.data.get("value")).isdigit() and str(request.data.get("tlg_id")).isdigit():

            # Получаем объект юзера и меняем ему баланс
            user_obj = TlgUser.objects.get(tlg_id=request.data.get("tlg_id"))
            if request.data.get("action") == '+':
                user_obj.balance = float(user_obj.balance) + float(request.data.get("value"))
            elif request.data.get("action") == '-':
                user_obj.balance = float(user_obj.balance) - float(request.data.get("value"))
            user_obj.save()
            return Response(status.HTTP_200_OK)

        else:
            logger.warning('Данные от REDIRECT_BOT об изменении баланса не прошли валидацию.')
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
                        'short_link_service': i_link.get('short_link_service'),
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


class PaymentsView(APIView):
    """
    Вьюшка для создания и обновления записей в таблице Payments.
    """
    def get(self, request):
        """
        GET запрос. Принимает tlg_id, отдаёт крайний неархивный платёж для этого юзера.
        """
        logger.info(f'Получен запрос от REDIRECT_BOT о получении инфы о записи из т.Payments')

        # Получаем крайнюю неархивную запись о платеже
        if str(request.query_params.get('tlg_id')).isdigit():
            tlg_user = TlgUser.objects.get(tlg_id=request.query_params.get('tlg_id'))
            payment_obj = Payments.objects.filter(tlg_id=tlg_user, archived=False).first()
            serializer_obj = PaymentsModelSerializer(instance=payment_obj, many=False).data
            return Response(serializer_obj, status.HTTP_200_OK)

        # Удаляем запись о платеже из БД
        elif request.query_params.get('payment_for_dlt_id'):
            payment_obj = Payments.objects.get(bill_id=request.query_params.get('payment_for_dlt_id'))
            payment_obj.archived = True
            payment_obj.save()
            return Response(status.HTTP_200_OK)

        else:
            logger.warning(f'Данные от REDIRECT_BOT на получение/удаление инфы о счёте не валидны.\n'
                           f'Параметры запроса: {request.query_params}')
            return Response({'result': 'Переданные данные не прошли валидацию.'}, status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        """
        POST запрос.
            tlg_id = serializers.CharField(max_length=25) - TG ID юзера
            pay_system_type = serializers.CharField(max_length=7) - Тип системы платежей
                                                                    (допустимые значения: qiwi, crystal, to_card)
            amount = serializers.CharField(max_length=15) - Сумма платежа в виде строки, но в формате '12345678.09'
            bill_id = serializers.CharField(max_length=350) - ID счёта на оплату
            bill_status = serializers.BooleanField() - Статус счёта (True/False - оплачен или нет)
        """
        logger.info(f'Получен запрос от REDIRECT_BOT о создании записи в т.Payments')

        serializer = PaymentsSerializer(data=request.data, many=False)
        if serializer.is_valid():
            tlg_user = TlgUser.objects.get(tlg_id=request.data.get('tlg_id'))
            payment_obj = Payments.objects.get_or_create(
                bill_id=serializer.data.get('bill_id'),
                defaults={
                    'tlg_id': tlg_user,
                    'pay_system_type': request.data.get('pay_system_type'),
                    'amount': float(request.data.get('amount')),
                    'bill_id': request.data.get('bill_id'),
                    'bill_expire_at': request.data.get('bill_expire_at'),
                    'bill_url': request.data.get('bill_url'),
                }
            )
            if not payment_obj[1]:  # Если объект не был создан, а был получен
                payment_obj[0].bill_status = request.data.get('bill_status')  # Обновляем статус счёта
                payment_obj[0].archived = True  # Переносим счёт в архив
                payment_obj[0].save()

            # Переносим в архив те платежи, которые уже устарели
            all_not_arcived_payments = Payments.objects.filter(archived=False)
            for i_payment in all_not_arcived_payments:
                if i_payment.bill_expire_at < datetime.datetime.now(pytz.timezone('Europe/Moscow')):
                    i_payment.archived = True
                    i_payment.save()

            logger.success(f"Успешное {'создание' if payment_obj[1] else 'обновление'} счёта.")
            serialized_obj = PaymentsSerializer(instance=payment_obj[0], many=False).data
            return Response(serialized_obj, status.HTTP_200_OK)

        else:
            logger.warning(f'Данные от REDIRECT_BOT на создание/обновление счёта не валидны.\n'
                           f'Запрос: {request.data}')
            return Response({'result': 'Переданные данные не прошли валидацию.'}, status.HTTP_400_BAD_REQUEST)
