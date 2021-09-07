import datetime
from json import JSONDecodeError
import logging
from typing import Optional, Union

import requests


# TODO: remove test data
TEST_CATEGORIES = [
    dict(id='EVENTS', name='Мероприятия'),
    dict(id='INTROS', name='Внедрения'),
    dict(id='OPENING', name='Открытие кода и данных'),
    dict(id='ORG', name='Дела организаций'),
    dict(id='DIY', name='DIY'),
    dict(id='LAW', name='Юридические вопросы'),
    dict(id='KnD', name='Ядро и дистрибутивы'),
    dict(id='SPECIAL', name='Специальное'),
    dict(id='EDUCATION', name='Обучение'),
    dict(id='DATABASES', name='Базы данных'),
    dict(id='MULTIMEDIA', name='Мультимедиа'),
    dict(id='MOBILE', name='Мобильные'),
    dict(id='SECURITY', name='Безопасность'),
    dict(id='SYSADM', name='Системное администрирование'),
    dict(id='DEVOPS', name='DevOps'),
    dict(id='DATA_SCIENCE', name='AI & Data Science'),
    dict(id='WEB', name='Web'),
    dict(id='DEV', name='Для разработчиков'),
    dict(id='TESTING', name='Тестирование'),
    dict(id='HISTORY', name='История'),
    dict(id='MANAGEMENT', name='Менеджмент'),
    dict(id='USER', name='Пользовательское'),
    dict(id='GAMES', name='Игры'),
    dict(id='HARDWARE', name='Железо'),
    dict(id='MISC', name='Разное'),
]


log = logging.getLogger('fngs')


def now():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')


class Fngs:
    def __init__(self, endpoint: str, username: str, password: str):
        self.endpoint = endpoint
        self.auth = dict(username=username, password=password)
        self.headers = None

    def fetch_token(self):
        token = requests.post(self.endpoint + 'token/', data=self.auth).json()['access']
        self.headers = dict(Authorization=f'Bearer {token}')

    def request(self, endpoint: str, method: str, query: dict = None, data: dict = None) -> Optional[requests.Response]:
        url = f'{self.endpoint}{endpoint}/'
        r = None

        if query:
            url += '?' + '&'.join([f'{k}={v}' for k, v in query.items()])
        log.debug('request: %s %s data=%s', method.upper(), url, data)

        if method == 'get':
            r = requests.get(url, headers=self.headers)
        elif method == 'post':
            r = requests.post(url, headers=self.headers, data=data)
        elif method == 'patch':
            r = requests.patch(url, headers=self.headers, data=data)

        if r is not None:
            r.raise_for_status()

        return r

    def register_user(self, tid: int, username: str) -> Optional[int]:
        try:
            r = self.request('telegram-bot-user', 'post', data=dict(tid=tid, username=username))
            log.info('user %i: %s registered', tid, username)
            return r.json()['id']
        except requests.HTTPError as e:
            log.warning("user %i: %s already registered: %s", tid, username, e.response.json()['tid'][0])
            return None

    def fetch_user_id(self, tid: int, username: str) -> int:
        r = self.request('telegram-bot-user-by-tid', 'get', query=dict(tid=tid))
        user_id = r.json()['id']
        log.info("user %i: %s id=%i", tid, username, user_id)
        return user_id

    def fetch_news(self, tid: int, username: str) -> dict:
        try:
            user_id = self.fetch_user_id(tid, username)
        except (requests.HTTPError, JSONDecodeError, KeyError):
            user_id = self.register_user(tid, username)

        r = self.request('telegram-bot-one-random-not-categorized-foss-news-digest-record', 'get',
                         query={'tbot-user-id': user_id})
        try:
            news = r.json()[0]
            log.info("user %i: fetched news=%i title='%s'", tid, news['id'], news['title'])
        except (JSONDecodeError, IndexError):
            news = {}
            log.info("user %i: no news for %s", tid, username)

        return news

    def fetch_categories(self) -> list:
        # TODO: replace test data with real request
        # r = self.request('telegram-bot-categories', 'get')
        # categories = r.json()
        categories = TEST_CATEGORIES
        log.info('fetched categories')
        return categories

    def send_digest_data(self, tid: int, username: str, news_id: int, state: str = 'null') -> int:
        r = self.request('telegram-bot-digest-record-categorization-attempt', 'post', data=dict(
            dt=now(),
            telegram_bot_user=self.fetch_user_id(tid, username),
            digest_record=news_id,
            estimated_state=state,
        ))
        attempt_id = r.json()['id']
        log.info('user %i: sent attempt id=%i news=%i state=%s', tid, attempt_id, news_id, state)
        return attempt_id

    def update_digest_data(self, tid: int, attempt_id: int, field: str, value: Union[bool, int, str]) -> None:
        self.request('telegram-bot-digest-record-categorization-attempt', 'patch',
                     data={'id': attempt_id, field: value})
        log.info('user %i: updated attempt id=%i %s=%s', tid, attempt_id, field, value)
