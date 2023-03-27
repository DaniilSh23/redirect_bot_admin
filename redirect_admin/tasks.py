import os
import random
import string
import requests
from celery import shared_task
from loguru import logger

from redirect_admin.models import LinkSet, Links, RedirectBotSettings


@shared_task
def wrap_links_in_redirect(link_set_id):
    """
    Отложенная задачка Celery, которая берёт ссылки и оборачивает их в редирект.
    Работает с Кеитаро, работает с нужным сервисом сокращения ссылок,
    а также наполняет БД новыми данными для ссылок.
    По итогу происходит отправка файла со ссылками юзеру от лица бота.
    """
    # Получаем набор ссылок и отфильтровываем ссылки, которые в него входят
    link_set_obj = LinkSet.objects.get(id=link_set_id)
    links_lst = Links.objects.filter(link_set=link_set_obj)

    logger.info(f'СТАРТ ОБЁРТКИ ССЫЛОК ДЛЯ {link_set_obj.tlg_id} '
                f'| НАБОР ССЫЛОК C ID == {link_set_obj.id}')

    # Итерируемся по списку ссылок
    for i_link in links_lst:
        logger.info(f'Ссылка {i_link.link}')

        # Вызываем функцию, которая кинет запрос к кейтаро и вернёт нам ID компании и редирект-ссылку
        keitaro_answer = create_company_in_keitaro(tlg_id=i_link.tlg_id.tlg_id, link_id=i_link.id,
                                                   link=i_link.link)
        if not keitaro_answer:  # Обработка неудачного ответа KEITARO
            logger.warning(f'Не удался запрос к KEITARO для ссылки {i_link.link}, {i_link.tlg_id}.')
            continue

        # Делаем редиректы
        redirect_links_with_utm = []  # Список для редирект-ссылок с utm метками
        for j_numb in range(i_link.redirect_numb):  # Выполняем итерации по кол-во редиректов
            logger.info(f'Делаем {j_numb + 1}-й редирект')
            utm_label = ''
            symbols_str = ''.join([string.ascii_letters, string.digits])  # Берём буквы и цифры
            for _ in range(random.randint(3, 91)):  # Рандомно совершаем от 3 до 91 итерации
                utm_label = ''.join([utm_label, random.choice(symbols_str)])  # Создаём UTM метку для ссылки
            # Записываем ссылку в общий список
            redirect_links_with_utm.append(f'{keitaro_answer[0]}?utm={utm_label}_LNKID{i_link.id}_RDRCTNMB{j_numb + 1}')

        # Сокращаем ссылки
        short_links = []
        numb_of_short_links = 0
        for k_redirect_link in redirect_links_with_utm:
            k_short_link = link_shortening(service_name=i_link.short_link_service,
                                           link_to_short=k_redirect_link)  # Запрос к сервису сокращалок

            if not k_short_link:  # Обработка неудачного запроса к сервису сокращения ссылок
                logger.warning(f'Не удался запрос к сервису сокращения ссылок {i_link.short_link_service}.'
                               f'Редирект-ссылка: {k_redirect_link} | Оригинальная ссылка: {i_link.link}')
                continue

            short_links.append(k_short_link)
            numb_of_short_links += 1

        # Обновляем данные в БД о ссылке
        i_link.company_id = keitaro_answer[1]
        i_link.redirect_links = ' '.join(redirect_links_with_utm)
        i_link.short_links = ' '.join(short_links)
        i_link.save()

        # Снимаем деньги с баланса
        tariff = RedirectBotSettings.objects.get(key='tariff').value
        user_obj = i_link.tlg_id
        user_obj.balance = float(user_obj.balance) - (float(tariff) * numb_of_short_links)
        user_obj.save()

    # Формируем файл и отправляем его юзеру от лица бота
    send_to_tlg_rslt = send_result_file_to_tlg(link_set_id=link_set_id)
    if send_to_tlg_rslt:
        logger.success(f'УСПЕШНАЯ ОТРАБОТАНО ДЛЯ {link_set_obj.tlg_id} '
                       f'| НАБОР ССЫЛОК C ID == {link_set_obj.id}')


def create_company_in_keitaro(tlg_id, link_id, link):
    """
    Создаём в Кеитаро компанию для каждой оригинальной ссылки.
    """
    url = "http://185.198.167.20/admin/?object=campaigns.create"
    querystring = {"object": "campaigns.create"}
    payload = {
        # alias - какое-то сокращённое название, но эта фигня должна быть уникальной
        "alias": f"REDIRECT_BOT---TlgUserID__{tlg_id}---LinkID__{link_id}",
        "state": "active",
        "type": "position",
        "cookies_ttl": 999999,
        "uniqueness_method": "ip_ua",
        "cost_type": "CPC",
        "cost_auto": True,
        "uniqueness_use_cookies": True,
        "domain_id": 5,
        "cost_currency": "RUB",
        "streams": [
            {
                "uid": 1679385901928,
                "type": "forced",
                "state": "active",
                "name": "Bot Protection",
                "schema": "action",
                "action_type": "campaign",
                "collect_clicks": True,
                "action_payload": 19,
                "filter_or": False,
                "filters": [
                    {
                        "name": "bot",
                        "mode": "accept",
                        "payload": None
                    }
                ],
                "position": 1,
                "weight": 0
            },
            {
                "uid": 1679385933495,
                "name": "Flow 2",
                "position": 2,
                "weight": 100,
                "schema": "redirect",
                "type": "regular",
                "action_type": "http",
                "state": "active",
                "campaign_id": None,
                "collect_clicks": True,
                "filter_or": False,
                "filters": [],
                "triggers": [],
                "postbacks": [],
                "action_payload": f"{link}"  # Здесь также ставим ссылку
            }
        ],
        "group_id": 3,  # 3 - ID группы "Помощь"
        "traffic_source_id": None,
        "parameters": {},
        # И здесь делаем по аналогии с alias
        "name": f"REDIRECT_BOT | USER_TG_ID: {tlg_id} | {link}",
        "bind_visitors": None
    }
    headers = {
        "cookie": "keitaro=jaa79fju1sil2umql63d2m6653",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json;charset=utf-8",
        "Origin": "http://185.198.167.20",
        "Connection": "keep-alive",
        "Referer": "http://185.198.167.20/admin/",
        "Cookie": "states=v1eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbiI6IjhkMTk0NjRiMTY3ZTZkMjljZTQ5NGFhYWRjNGJm"
                  "NWZkIiwicGFzc3dvcmQiOiIlMjQyeSUyNDEwJTI0bDZvQmFTaFN6TTl0Lm9ISDBjR1k1LkQybUh6dlR6Ljl5aGVPNSUyRkRtYWl"
                  "6Mlp4LkxEbTNBeSIsInRpbWVzdGFtcCI6MTY3OTEzNDEzNH0.PCDnkcFsZWg7C5fuGDsswE6ohyr2s1DnYETg"
                  "17SJp_U; streamsView=true; streamsSharesVisible=false; keitaro=c6mtduund16i8qdj8tt5ef52m1"
    }
    response = requests.post(url, json=payload, headers=headers, params=querystring)
    if response.status_code != 200:
        logger.error(f'НЕУДАЧНЫЙ ЗАПРОС К КЕИТАРО. Ответ хоста: {response.json()}')
        return False

    redirect_link = ''.join([response.json().get('domain'), response.json().get('alias')])
    company_id = response.json().get('id')
    return redirect_link, company_id


def link_shortening(service_name, link_to_short):
    """
    Функция для сокращения ссылок.
    Принимает параметры:
        service_name - название сервиса по сокращению ссылок,
        link_to_short - ссылка для сокращения.
    Функция выполняет запрос и возвращает сокращённую ссылку. При неудачном запросе возвращает False.
    """
    if service_name == 'cutt.ly':
        api_token = RedirectBotSettings.objects.get(key='cutt.ly_api_token')
        response = requests.get(f'http://cutt.ly/api/api.php?key={api_token}&short={link_to_short}')
        short_lnk = response.json().get("url").get('shortLink')

    elif service_name == 'cutt.us':
        response = requests.get(f'https://cutt.us/api.php?url=dyatel.pro')
        short_lnk = response.text

    elif service_name == 'clck.ru':
        response = requests.get(f'https://clck.ru/--?url={link_to_short}')
        short_lnk = response.text

    elif service_name == 'kortlink.dk':
        response = requests.post(url=f'https://kortlink.dk/lavkort.php?url={link_to_short}&Submit=Lav+linket+kort')
        # в ответе нас редиректят на ссылку, у которой нам нужен пар-р id(он там будет один)
        short_lnk = response.url.split('?')[1].split('=')[1]
        short_lnk = f'https://kortlink.dk/{short_lnk}'  # Собираем сами ссылку

    elif service_name == 'gg.gg':
        url = "https://gg.gg/create"
        payload = "custom_path=&use_norefs=0&long_url=https://dyatel.pro&app=site&version=0.1"
        headers = {
            "cookie": "__ddg1_=SLj1qFv2FswCgHiql9PG; ci_session=a%253A5%253A%257Bs%253A10%253A%2522"
                      "session_id%2522%253Bs%253A32%253A%252274f9910433781230c8d921855c451daf%2522%253Bs%"
                      "253A10%253A%2522ip_address%2522%253Bs%253A12%253A%2522186.2.160.64%2522%253Bs%253A10%253A%2522"
                      "user_agent%2522%253Bs%253A78%253A%2522Mozilla%252F5.0%2B%2528X11%253B%2BUbuntu%253B%2B"
                      "Linux%2Bx86_64%253B%2Brv%253A109.0%2529%2BGecko%252F20100101%2BFirefox%252F110.0%2522%253Bs"
                      "%253A13%253A%2522last_activity%2522%253Bi%253A1679907604%253Bs%253A9%253A%2522"
                      "user_data%2522%253Bs%253A0%253A%2522%2522%253B%257D1efff8b53a312ebb3a50f9eae855b"
                      "ab5; gg_token=afc05dc12a3ac8386c74e10c664adb0a6415ac6cb2a4d6.83342873",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/110.0",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = requests.post(url, data=payload, headers=headers)
        short_lnk = response.text

    elif service_name == 't9y.me':
        url = "https://api.t9y.me/v1/shorten-url"
        payload = {"url": "https://dyatel.pro"}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        short_lnk = response.json().get('data').get('shortUrl')

    else:  # Иначе, если service_name не определён
        logger.warning(f'Не определён сервис для сокращения ссылок. service_name=={service_name}')
        return False

    if response.status_code != 200:  # Проверка на отрицательный ответ хоста
        logger.warning(f'Неудачный запрос для сокращения ссылки к сервису {service_name}. Ссылка: {link_to_short}')
        return False
    else:
        return short_lnk


def send_result_file_to_tlg(link_set_id):
    """
    Функция для записи ссылок в файл и отправки его юзеру в телеграм.
    Параметры:
        link_set_id - ID набора ссылок
    """
    # Получаем данные из БД
    link_set_obj = LinkSet.objects.get(id=link_set_id)
    links_lst = Links.objects.filter(link_set=link_set_obj)

    logger.info(f'Запуск функции записи и отправки файла в TG для юзера TG_ID == {link_set_obj.tlg_id.tlg_id}')

    # Записываем файл
    file_path = f'media/files_to_send/links_rslt_{link_set_obj.tlg_id.tlg_id}.txt'
    with open(file_path, mode='w', encoding='utf-8') as rslt_file:
        for i_link in links_lst:
            logger.info(f'Записываем в файл данные для ссылки {i_link.link}')
            short_links = i_link.short_links.replace(' ', '\n\t')  # Заменяем пробелы на перенос строки
            rslt_file.write(f'Исходная ссылка:\n{i_link.link}\n\nID для проверки статистики:\n{i_link.company_id}\n\n'
                            f'\t{short_links}\n{"=" * 40}\n')

    # Отправляем файл в телеграм
    bot_token = RedirectBotSettings.objects.get(key='bot_token').value
    url = f'https://api.telegram.org/bot{bot_token}/sendDocument'

    with open(file_path, 'rb') as file:  # Открываем файл в бинарном режиме и считываем в переменную
        file_content = file.read()

    data = {'chat_id': link_set_obj.tlg_id.tlg_id}
    files = {'document': ('redirect_links.txt', file_content)}
    response = requests.post(url=url, data=data, files=files)  # Выполняем запрос на отправку файла

    if response.status_code != 200:  # Обработка неудачного запроса на отправку
        logger.error(f'Не удалось отправить файл в телеграм для юзера TG ID:{link_set_obj.tlg_id.tlg_id}!\n'
                     f'Запрос: url={url} | data={data} | файл доступен по file_path={file_path}\n'
                     f'Ответ:{response.json()}')
        return False

    logger.success(f'Файл с редирект-ссылками отправлен юзеру TG ID == {link_set_obj.tlg_id.tlg_id}. '
                   f'Удаляю файл с диска.')
    os.remove(path=file_path)  # Удаляем файл с диска
    return True
