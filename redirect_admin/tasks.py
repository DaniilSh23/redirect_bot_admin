from celery import shared_task


@shared_task
def wrap_links_in_redirect(link_set_id):
    """
    Отложенная задачка Celery, которая берёт ссылки и оборачивает их в редирект.
    Работает с Кеитаро, работает с нужным сервисом сокращения ссылок,
    а также наполняет БД новыми данными для ссылок.
    По итогу происходит отправка файла со ссылками юзеру от лица бота.
    """
    print('hello world', link_set_id)
    # TODO: 1) Создать в кейтаро компании под каждую оригинальную ссылку
    #  2) Сократить ссылки-редиректы с помощью нужного сервиса
    #  3) Отправить файл от лица бота юзеру

    # Надо получить набор ссылок, из него вытянуть юзера и по нему отфильтровать ссылки.
    # Дальше итерироваться по ссылкам и на каждой итерации кидать запрос к кейтаро для создания компании
    # в ответе получать ID компании и собранную ссылку,
    # затем в этом коде формировать для неё utm метки, по числу редиректов
    # потом каждую из этих "помеченных" ссылок скармливать сокращателю ссылок
    # ну и не забывать на разных этапах обновлять данные в БД. Но не слишком часто, а то у нас же sqlite
    create_company_in_keitaro(tlg_id, link_id, link)


def create_company_in_keitaro(tlg_id, link_id, link):
    """
    Создаём в Кеитаро компанию для каждой оригинальной ссылки.
    """
    import requests

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
        "name": f"REDIRECT_BOT | USER_TG_ID: 12345 | https://test_link.com",
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

    print(response.json())
    # TODO: тут из ответа собирать ссылку и return'ом выкидывать её из функции вместе с ID компании