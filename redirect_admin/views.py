import datetime
import json

from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib import messages as err_msgs
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request as DRFRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from redirect_admin.models import (
    TlgUser,
    RedirectBotSettings,
    Links,
    LinkSet,
    Payments,
    Transaction,
    InterfaceLanguages,
)
from redirect_admin.serializers import (
    TlgUserSerializer,
    RedirectBotSettingsSerializer,
    LinksSerializer,
    LinkSetSerializer,
    PaymentsSerializer,
    PaymentsModelSerializer,
    TransactionSerializer,
    LanguageInterfaceInSerializer,
)
from redirect_admin.forms import BaseTlgIdForm, UserDomainForm, UserTransferForm
from redirect_admin.saga import AddUserDomainSaga
from redirect_admin.services import UserDomainService, TransferUserService
from redirect_bot_admin.settings import MY_LOGGER, BOT_TOKEN


class TlgUserView(APIView):
    """
    Вьюшка для обработки запросов, связанных с моделью TlgUser.
    """

    def get(self, request, format=None):
        """
        Обработка GET запроса:
            ?tlg_id=.. - получение данных об одном пользователе по tlg_id
        """
        tlg_id = request.query_params.get("tlg_id")
        if tlg_id and str(tlg_id).isdigit():
            try:
                tlg_user_obj = TlgUser.objects.get(tlg_id=tlg_id)
            except Exception as error:
                MY_LOGGER.error(
                    f"Не удалось получить объект TlgUser, запрошен по tlg_id={tlg_id}\nТекст ошибки: {error}"
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)

            bot_user_serializer = TlgUserSerializer(tlg_user_obj, many=False).data
            MY_LOGGER.success(
                f"REDIRECT_BOT | Успешно обработан GET запрос на получение объекта TlgUser"
            )
            return Response(bot_user_serializer, status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(
                f"REDIRECT_BOT | Неверные параметры запроса для получения объекта TlgUser"
            )
            return Response(
                {"result": "Неверные параметры запроса"}, status.HTTP_400_BAD_REQUEST
            )

    def post(self, request, format=None):
        """
        Обработка POST запроса.
        """
        MY_LOGGER.info(f"Получен запрос от REDIRECT_BOT на запись пользователя.")
        serializer = TlgUserSerializer(data=request.data)
        if serializer.is_valid():
            tlg_user_obj = TlgUser.objects.get_or_create(
                tlg_id=serializer.data.get("tlg_id"), defaults=serializer.data
            )
            MY_LOGGER.success(
                f"Пользователь REDIRECT_BOT c TG_ID == {serializer.data.get('tlg_id')} "
                f"{'был создан' if tlg_user_obj[1] else 'уже есть в БД'}."
            )
            result_object = TlgUserSerializer(tlg_user_obj[0], many=False).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT на запись пользователя не прошли валидацию."
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию"},
                status.HTTP_400_BAD_REQUEST,
            )


class InterfaceLanguage(APIView):
    """
    Вьюшки для работы с языками интерфейса бота.
    """

    def get(self, request: DRFRequest):
        """
        Вьюшка для получения языка интерфейса пользователя бота или получения всех доступных языков интерфейса.
            ?tlg_id=... - получение данных об одном пользователе по tlg_id
            Если tlg_id не указан, то GET запрос вернет все доступные языки интерфейса.
        """
        MY_LOGGER.info(
            f"Получен GET запрос на вьюшку InterfaceLanguage | {request.GET}"
        )
        tlg_id = request.query_params.get("tlg_id")

        # Если не указан tlg_id, то возвращаем все доступные языки интерфейса
        if not tlg_id:
            languages = InterfaceLanguages.objects.all()
            response_data = list()
            for i_lang in languages:  # Собираем данные для ответа - добавляем все языки
                response_data.append(
                    {
                        "language_code": i_lang.language_code,
                        "language": i_lang.language,
                    }
                )
            MY_LOGGER.success(
                f"REDIRECT_BOT | Успешно обработан GET запрос на получение всех языков интерфейса"
            )
            return Response(data=response_data, status=status.HTTP_200_OK)

        # Проверяем, что tlg_id - это число
        elif str(tlg_id).isdigit():
            try:
                tlg_user_obj = TlgUser.objects.get(tlg_id=tlg_id)
            except Exception as error:
                MY_LOGGER.error(
                    f"Не удалось получить объект TlgUser, запрошен по tlg_id={tlg_id}\nТекст ошибки: {error}"
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if not tlg_user_obj.interface_language:
                default_lang = InterfaceLanguages.objects.filter(
                    default_language=True
                ).first()
                MY_LOGGER.debug(
                    f"У юзера не установлен язык, ставим дефолтный: {default_lang!r}"
                )
                tlg_user_obj.interface_language = default_lang
                tlg_user_obj.save()

            response_data = {
                "tlg_id": tlg_user_obj.tlg_id,
                "language_code": tlg_user_obj.interface_language.language_code
                if tlg_user_obj.interface_language
                else None,
                "language": tlg_user_obj.interface_language.language
                if tlg_user_obj.interface_language
                else None,
            }
            MY_LOGGER.success(
                f"REDIRECT_BOT | Успешно обработан GET запрос на получение языка интерфейса юзера "
                f"tlg_id=={tlg_id}"
            )
            return Response(data=response_data, status=status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(
                f"REDIRECT_BOT | Неверные параметры запроса для получения языка интерфейса юзера"
            )
            return Response(
                {"result": "Неверные параметры запроса"}, status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=LanguageInterfaceInSerializer, responses=str, methods=["post"]
    )
    def post(self, request: DRFRequest):
        """
        Вьюшка для обработки POST запроса на изменение языка интерфейса пользователя бота.
        """
        MY_LOGGER.info(
            f"Получен POST запрос на вьюшку InterfaceLanguage | {request.POST}"
        )

        ser = LanguageInterfaceInSerializer(data=request.data)

        # Проверка токена
        if BOT_TOKEN != request.data.get("token"):
            MY_LOGGER.warning(
                f"Неверный токен запроса. {BOT_TOKEN} != {request.data.get('token')}"
            )
            return Response(status=403, data={"result": "Неверный токен"})

        if ser.is_valid():
            validated_data = ser.validated_data

            # Пробуем получить объект пользователя
            try:
                tlg_user_obj = TlgUser.objects.get(tlg_id=validated_data.get("tlg_id"))
            except Exception as error:
                MY_LOGGER.error(
                    f"Не удалось получить объект TlgUser, запрошен по tlg_id={validated_data.get('tlg_id')}\n"
                    f"Текст ошибки: {error}"
                )
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={
                        "err": f"Не найден юзер с TG ID == {validated_data.get('tlg_id')}"
                    },
                )

            # Пробуем получить запись в БД с переданным в запросе языком интерфейса
            try:
                interface_language = InterfaceLanguages.objects.get(
                    language_code=validated_data.get("language_code")
                )
            except Exception as error:
                MY_LOGGER.error(
                    f"Не удалось получить объект InterfaceLanguages, запрошен по "
                    f"language_code={validated_data.get('language_code')}\nТекст ошибки: {error}"
                )
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={
                        "err": f"Не найден язык интерфейса с кодом == {validated_data.get('language_code')}"
                    },
                )

            # Изменяем язык интерфейса пользователя
            tlg_user_obj.interface_language = interface_language
            tlg_user_obj.save()
            MY_LOGGER.success(
                f"Язык интерфейса успешно установлен! | {tlg_user_obj}, {interface_language}"
            )
            return Response(status=200, data={"result": "OK!"})

        else:
            MY_LOGGER.warning(
                f"Невалидные данные запроса. | Запрос: {request.data} | Ошибки: {ser.errors}"
            )
            return Response(
                status=400, data={"result": f"Неудачный запрос | {ser.errors}"}
            )


class ChangeBalance(APIView):
    """
    Вьюха для изменения баланса.
    """

    def post(self, request, format=None):
        MY_LOGGER.info(
            f"Получен запрос от редирект бота на изменение баланса юзера TG ID == {request.data.get('tlg_id')}"
            f" на {request.data.get('action')}{request.data.get('value')} руб."
        )

        # Проверка данных, которые пришли в запросе
        if (
            (request.data.get("action") == "+" or request.data.get("action") == "-")
            and str(request.data.get("value")).isdigit()
            and str(request.data.get("tlg_id")).isdigit()
        ):
            # Получаем объект юзера и меняем ему баланс
            user_obj = TlgUser.objects.get(tlg_id=request.data.get("tlg_id"))
            if request.data.get("action") == "+":
                user_obj.balance = float(user_obj.balance) + float(
                    request.data.get("value")
                )
                transaction_type = "replenishment"
            elif request.data.get("action") == "-":
                user_obj.balance = float(user_obj.balance) - float(
                    request.data.get("value")
                )
                transaction_type = "write-off"

            # Создаём транзакцию под это дело
            Transaction.objects.create(
                user=user_obj,
                transaction_type=transaction_type,
                amount=float(request.data.get("value")),
                description=f"{request.data.get('description')} Баланс: {user_obj.balance} руб.",
            )
            user_obj.save()
            return Response(status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(
                "Данные от REDIRECT_BOT об изменении баланса не прошли валидацию."
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию"},
                status.HTTP_400_BAD_REQUEST,
            )


class GetSettingsView(APIView):
    """
    Вьюшка для обработки запросов, связанных с получением ключей из таблицы RedirectBotSettings.
    """

    def get(self, request, format=None):
        """
        Обработка GET запроса для получения данных по ключу
        ?key - ключ настройки
        """
        redirect_bot_settings_obj = RedirectBotSettings.objects.filter(
            key=request.GET.get("key")
        )
        redirect_bot_settings_serializer = RedirectBotSettingsSerializer(
            redirect_bot_settings_obj, many=True
        ).data
        return Response(redirect_bot_settings_serializer, status.HTTP_200_OK)


class GetLinkOwner(APIView):
    """
    Вьюшка для полуения владельца ссылки.
    """

    def get(self, request, format=None):
        """
        Обработка запроса на получение владельца ссылки.
        Принимаем company_id ссылки и достаём TG ID владельца.
        Возвращаем TG ID владельца.
        """
        MY_LOGGER.info(f"Принят запрос от REDIRECT_BOT на получение ссылки.")
        if request.query_params.get(
            "company_id"
        ).isdigit():  # Проверка, что пришли цифры в запросе
            # Достаём ссылку из БД
            try:
                link_object = Links.objects.get(
                    company_id=request.query_params.get("company_id")
                )
            except ObjectDoesNotExist:
                MY_LOGGER.warning(
                    f"Ссылка с company_id == {request.query_params.get('company_id')} не найдена в БД."
                )
                return Response(
                    {"result": "Объект ссылки не найден."}, status.HTTP_404_NOT_FOUND
                )
            except MultipleObjectsReturned:
                MY_LOGGER.warning(
                    f"Получено более одной ссылки с company_id == "
                    f"{request.query_params.get('company_id')}"
                )
                link_object = Links.objects.filter(
                    company_id=request.query_params.get("company_id")
                ).first()

            return Response(
                {"link_owner": link_object.tlg_id.tlg_id}, status.HTTP_200_OK
            )
        else:
            MY_LOGGER.warning(
                f"Получен невалидный ID ссылкии от REDIRECT_BOT.\nЗапрос: {request.data}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию"},
                status.HTTP_400_BAD_REQUEST,
            )


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
        MY_LOGGER.info(f"Получен запрос от REDIRECT_BOT на создание/обновление ссылки.")
        serializer = LinksSerializer(data=request.data, many=True)
        if serializer.is_valid():
            rslt_objects = []
            for i_link in serializer.data:
                tlg_user = TlgUser.objects.get(tlg_id=i_link.get("tlg_id"))
                link_set_obj = LinkSet.objects.get(id=i_link.get("link_set_id"))
                link_obj = Links.objects.update_or_create(
                    id=i_link.get("id"),
                    defaults={
                        "tlg_id": tlg_user,
                        "link": i_link.get("link"),
                        "link_set": link_set_obj,
                        "redirect_numb": i_link.get("redirect_numb"),
                        "short_link_service": i_link.get("short_link_service"),
                    },
                )
                MY_LOGGER.success(
                    f"REDIRECT_BOT | Ссылка {i_link.get('link')}"
                    f" для юзера TG_ID == {i_link.get('tlg_id')} "
                    f"была {'создана' if link_obj[1] else 'обновлёна'} {link_obj[0].id}."
                )
                rslt_objects.append(link_obj[0])

            result_object = LinksSerializer(rslt_objects, many=True).data
            return Response(result_object, status.HTTP_200_OK)
        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT на запись/обновление ссылки не валидны.\nЗапрос: {request.data}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию"},
                status.HTTP_400_BAD_REQUEST,
            )


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
        MY_LOGGER.info(
            f"Получен запрос от REDIRECT_BOT на создание/обновление набора ссылок."
        )
        serializer = LinkSetSerializer(data=request.data, many=False)
        if serializer.is_valid():
            tlg_user = TlgUser.objects.get(tlg_id=request.data.get("tlg_id"))
            link_set_obj = LinkSet.objects.update_or_create(
                id=serializer.data.get("id"),
                defaults={
                    "tlg_id": tlg_user,
                    "title": serializer.data.get("title"),
                },
            )
            MY_LOGGER.success(
                f"Успешное {'создание' if link_set_obj[1] else 'обновление'} набора ссылок."
            )
            serialized_obj = LinkSetSerializer(
                instance=link_set_obj[0], many=False
            ).data
            return Response(serialized_obj, status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT на создание/обновление набора ссылок не валидны.\n"
                f"Запрос: {request.data}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию."},
                status.HTTP_400_BAD_REQUEST,
            )


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

        MY_LOGGER.info(f"Получен запрос от REDIRECT_BOT для старта обёртки ссылок.")
        if str(request.data.get("link_set_id")).isdigit():
            wrap_links_in_redirect.delay(link_set_id=request.data.get("link_set_id"))
            MY_LOGGER.info(
                f"Запущена отложенная задача для обёртки ссылок "
                f"из набора с ID == {request.data.get('link_set_id')}"
            )
            return Response(status.HTTP_200_OK)
        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT для старта обёртки ссылок не валидны.\n"
                f"Запрос: {request.data}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию."},
                status.HTTP_400_BAD_REQUEST,
            )


class PaymentsView(APIView):
    """
    Вьюшка для создания и обновления записей в таблице Payments.
    """

    def get(self, request):
        """
        GET запрос. Принимает tlg_id, отдаёт крайний неархивный платёж для этого юзера.
        """
        MY_LOGGER.info(
            f"Получен запрос от REDIRECT_BOT о получении инфы о записи из т.Payments"
        )

        # Получаем крайнюю неархивную запись о платеже
        if str(request.query_params.get("tlg_id")).isdigit():
            tlg_user = TlgUser.objects.get(tlg_id=request.query_params.get("tlg_id"))
            payment_obj = (
                Payments.objects.filter(
                    tlg_id=tlg_user, archived=False, bill_status=False
                )
                .order_by("-created_at")
                .first()
            )

            # Если список пустой, то выдаём 404
            if not payment_obj:
                return Response(status.HTTP_404_NOT_FOUND)

            serializer_obj = PaymentsModelSerializer(
                instance=payment_obj, many=False
            ).data
            return Response(serializer_obj, status.HTTP_200_OK)

        # Удаляем запись о платеже из БД
        elif request.query_params.get("payment_for_dlt_id"):
            payment_obj = Payments.objects.get(
                bill_id=request.query_params.get("payment_for_dlt_id")
            )
            payment_obj.archived = True
            payment_obj.save()
            return Response(status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT на получение/удаление инфы о счёте не валидны.\n"
                f"Параметры запроса: {request.query_params}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию."},
                status.HTTP_400_BAD_REQUEST,
            )

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
        MY_LOGGER.info(f"Получен запрос от REDIRECT_BOT о создании записи в т.Payments")

        serializer = PaymentsSerializer(data=request.data, many=False)
        if serializer.is_valid():
            tlg_user = TlgUser.objects.get(tlg_id=request.data.get("tlg_id"))
            payment_obj = Payments.objects.get_or_create(
                bill_id=serializer.data.get("bill_id"),
                defaults={
                    "tlg_id": tlg_user,
                    "pay_system_type": request.data.get("pay_system_type"),
                    "amount": float(request.data.get("amount")),
                    "bill_id": request.data.get("bill_id"),
                    "bill_expire_at": request.data.get("bill_expire_at"),
                    "bill_url": request.data.get("bill_url"),
                },
            )
            if not payment_obj[1]:  # Если объект не был создан, а был получен
                payment_obj[0].bill_status = request.data.get(
                    "bill_status"
                )  # Обновляем статус счёта
                payment_obj[0].archived = True  # Переносим счёт в архив
                payment_obj[0].save()

            # Переносим в архив те платежи, которые уже устарели
            all_not_arcived_payments = Payments.objects.filter(archived=False)
            for i_payment in all_not_arcived_payments:
                if i_payment.bill_expire_at < datetime.datetime.now(
                    pytz.timezone("Europe/Moscow")
                ):
                    i_payment.archived = True
                    i_payment.save()

            MY_LOGGER.success(
                f"Успешное {'создание' if payment_obj[1] else 'обновление'} счёта."
            )
            serialized_obj = PaymentsSerializer(
                instance=payment_obj[0], many=False
            ).data
            return Response(serialized_obj, status.HTTP_200_OK)

        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT на создание/обновление счёта не валидны.\n"
                f"Запрос: {request.data}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию."},
                status.HTTP_400_BAD_REQUEST,
            )


class TransactionView(APIView):
    """
    Вьюшка для работы с транзакциями.
    """

    def get(self, request):
        """
        Запуск задачи Celery по формированию файла с транзакциями по конкретному юзеру и отправка его в телеграм.
        """
        from redirect_admin.tasks import send_transactions

        MY_LOGGER.info(f"Получен запрос от REDIRECT_BOT о получении транзакций.")

        if request.query_params.get("tlg_id").isdigit():
            send_transactions.delay(tlg_id=request.query_params.get("tlg_id"))
            return Response(status=status.HTTP_200_OK)

        else:
            return Response(
                {"result": "Переданные данные не прошли валидацию."},
                status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request):
        """
        В запросе должен прийти tlg_id, amount, description, transaction_type
        """
        MY_LOGGER.info(
            f"Получен запрос от REDIRECT_BOT о создании записи в т.Transaction"
        )

        serializer = TransactionSerializer(data=request.POST, many=False)
        if serializer.is_valid():
            try:
                user_obj = TlgUser.objects.get(
                    tlg_id=serializer.validated_data.get("tlg_id")
                )
                # Создаём транзакцию в БД
                transaction_obj = Transaction.objects.create(
                    user=user_obj,
                    transaction_type=serializer.validated_data.get("transaction_type"),
                    amount=serializer.validated_data.get("amount"),
                    description=f"{serializer.validated_data.get('description')} "
                    f"Баланс: {user_obj.balance} руб.",
                )
                return Response(
                    {
                        "result": f"Ok👌. Создана транзакция с ID == {transaction_obj.pk} "
                        f"для юзера с tlg_id == {transaction_obj.user.tlg_id}"
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as error:
                MY_LOGGER.warning(
                    f"Не удалось создать транзакцию для юзера с "
                    f"tlg_id == {serializer.validated_data.get('tlg_id')}. Текст ошибки: {error}"
                )
                return Response(
                    {
                        "error": f"При создании транзакции в БД произошла ошибка. Вот её текст: {error}"
                    },
                    status.HTTP_400_BAD_REQUEST,
                )

        else:
            MY_LOGGER.warning(
                f"Данные от REDIRECT_BOT на создание транзакций не валидны.\n"
                f"Запрос: {request.data}"
            )
            return Response(
                {"result": "Переданные данные не прошли валидацию."},
                status.HTTP_400_BAD_REQUEST,
            )


@csrf_exempt
def get_up_bot(request):
    """
    Вьюшка для восстановления бота после сноса. В теле принимает json с данными для восстановления
    """
    if request.method == "POST":
        MY_LOGGER.info(f"Получен запрос на вьюшку восстановления бота после сноса")
        recovery_token = RedirectBotSettings.objects.filter(key="recovery_token")[
            0
        ].value
        req_data = json.loads(request.body)

        if req_data.get("recovery_token") != recovery_token:
            MY_LOGGER.warning(
                f"Выполнен запрос к вьюшке восстановления бота с неверным recovery_token: "
                f"{request.POST.get('recovery_token')!r} | верное значение {recovery_token!r}"
            )
            return HttpResponse(status=403, content="у вас нет доступа")

        MY_LOGGER.debug(f"Удаляем всех админов")
        RedirectBotSettings.objects.filter(key="redirect_bot_admin").delete()
        for i_admin in req_data.get("redirect_bot_admin"):
            MY_LOGGER.debug(f"Создаём админа с ID == {i_admin!r}")
            RedirectBotSettings.objects.create(key="redirect_bot_admin", value=i_admin)

        for i_key in (
            "bot_token",
            "feedback_link",
            "support_username",
            "who_approves_payments",
        ):
            obj, created = RedirectBotSettings.objects.update_or_create(
                key=i_key, defaults={"key": i_key, "value": req_data.get(i_key)}
            )
            MY_LOGGER.debug(
                f"Ключ {i_key!r} {'обновлён' if created else 'создан'}. Значение {req_data.get(i_key)}"
            )
        return HttpResponse(status=200)

    else:
        return HttpResponse(status=405, content="недопустимый метод запроса")


class UserDomainView(View):
    """
    Вьюшка для работы с доменами пользователей.
    """

    def get(self, request: HttpRequest):
        """
        Рендерим страницу персональный доменов юзеров
        """
        MY_LOGGER.info(f"{request.method} запрос на UserDomainView | {request.GET}")
        tlg_id = request.GET.get("tlg_id")
        if not tlg_id:
            return HttpResponse(
                status=400, content="Пожалуйста, перейдите из Telegram."
            )

        # Достаем данные, необходимые для отображения на странице
        domain_records = UserDomainService.read_all_for_user(tlg_id=tlg_id)

        # Даем ответ на запрос
        context = {
            "domain_records": domain_records,
        }
        return render(request, template_name="user_domains.html", context=context)

    def post(self, request: HttpRequest):
        """
        Обработка запроса для создания записи UserDomain
        """
        MY_LOGGER.info(f"{request.method} запрос на UserDomainView | {request.POST}")

        form = UserDomainForm(request.POST)
        if not form.is_valid():
            MY_LOGGER.warning(f"Форма невалидна. Ошибка: {form.errors}")
            err_msgs.error(
                request, "Ошибка: Вы уверены, что открыли форму из Telegram?"
            )
            return redirect(to=reverse_lazy("redirect_admin:user_domain"))

        # Забираем данные из формы и выполняем сагу на создание домена
        tlg_id = form.cleaned_data.get("tlg_id")
        domain = form.cleaned_data.get("domain")
        add_saga = AddUserDomainSaga(user_tlg_id=tlg_id, domain=domain)
        result = add_saga.create_user_domain()
        if not result:
            err_msgs.error(
                request, "Не удалось создать домен, возможно ошибка с ClaudFlare"
            )

        redirect_url = f"{reverse_lazy('redirect_admin:user_domain')}?tlg_id={tlg_id}"
        return redirect(to=redirect_url)


class UserDomainDeleteView(View):
    """
    Вьюшка для удаления записи UserDomain
    """

    def post(self, request: HttpRequest, pk: int):
        """
        Обработка запроса для удаления записи UserDomain
        """
        MY_LOGGER.info(f"{request.method} запрос на UserDomainView | {pk}")

        form = BaseTlgIdForm(request.POST)
        if not form.is_valid():
            MY_LOGGER.warning(f"Форма невалидна. Ошибка: {form.errors}")
            err_msgs.error(
                request, "Ошибка: Вы уверены, что открыли форму из Telegram?"
            )
            return redirect(to=reverse_lazy("redirect_admin:user_domain"))

        user_domain = UserDomainService.read(pk=pk)
        UserDomainService.delete(record=user_domain)
        tlg_id = form.cleaned_data.get("tlg_id")
        redirect_url = f"{reverse_lazy('redirect_admin:user_domain')}?tlg_id={tlg_id}"
        return redirect(to=redirect_url)


@method_decorator(staff_member_required, name="dispatch")
class TransferUsersView(View):
    """
    Вьюшка для перемещения баланса, ссылок и прочего с одного аккаунта пользователя на другой.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Рендерим страницу для перемещения аккаунтов.
        """
        MY_LOGGER.info(f"{request.method} запрос на TransferUsersView | {request.GET}")
        return render(request, template_name="transfer_users.html")

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Выполняем перемещение данных с одного аккаунта на другой.
        """
        MY_LOGGER.info(f"{request.method} запрос на TransferUsersView | {request.POST}")

        # Валидация данных формы
        form = UserTransferForm(request.POST)
        if not form.is_valid():
            MY_LOGGER.warning(f"Форма невалидна. Ошибка: {form.errors}")
            err_msgs.error(
                request, "Ошибка: невалидные данные формы"
            )
            return redirect(to=reverse_lazy("redirect_admin:transfer_users"))

        old_tlg_id = form.cleaned_data.get("old_tlg_id")
        new_tlg_id = form.cleaned_data.get("new_tlg_id")

        # Вызов логики трансфера аккаунтов
        result = TransferUserService.transfer(old_tlg_id=old_tlg_id, new_tlg_id=new_tlg_id)
        if not result:
            MY_LOGGER.warning(f"Не удалось выполнить перенос данных между аккаунтами old_tlg_id=={old_tlg_id} и new_tlg_id=={new_tlg_id}")
            err_msgs.error(
                request, "Ошибка: неверные TELEGRAM ID."
            )
            return redirect(to=reverse_lazy("redirect_admin:transfer_users"))

        context = {
            "header_text": "Успешно",
            "header_description": f"Перенос данных с аккаунта {old_tlg_id} на аккаунт {new_tlg_id} выполнен успешно.",
            "button_text": "Окей",
        }
        return render(request, template_name="success.html", context=context)
