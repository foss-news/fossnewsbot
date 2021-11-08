"""FNGS API for fossnewsbot

This module implements FOSS News Gathering Server API calls for FOSS News Telegram Bot.
"""

#  Copyright (C) 2021 PermLUG
#
#  This file is part of fossnewsbot, FOSS News Telegram Bot.
#
#  fossnewsbot is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  fossnewsbot is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime
from functools import wraps
from json import JSONDecodeError
from logging import getLogger
from random import randint
from typing import Any, Callable, Optional, Union
from urllib.parse import urlencode

from aiogram.types import User
from requests import HTTPError, Response
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_toolbelt.sessions import BaseUrlSession

from cache import LRUCacheTTL, cached_property_with_ttl
from .config import config
from .i18n import LANGUAGES


# Default values
DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_RETRIES = 3
DEFAULT_GROUPS = ['users']

# News types and categories
# TODO: remove test data
TEST_TYPES = dict(
    NEWS=dict(en='News', ru='Новости'),
    ARTICLES=dict(en='Articles', ru='Статьи'),
    VIDEOS=dict(en='Videos', ru='Видео'),
    RELEASES=dict(en='Releases', ru='Релизы'),
    OTHER=dict(en='Other', ru='Прочее'),
)
TEST_CATEGORIES = dict(
    EVENTS=dict(en='Events', ru='Мероприятия'),
    INTROS=dict(en='Introductions', ru='Внедрения'),
    OPENING=dict(en='Opening', ru='Открытие кода и данных'),
    ORG=dict(en='Organizations', ru='Дела организаций'),
    DIY=dict(en='DIY', ru='DIY'),
    LAW=dict(en='Law & Legal', ru='Юридические вопросы'),
    KnD=dict(en='Kernel & Drivers', ru='Ядро и дистрибутивы'),
    SPECIAL=dict(en='Special', ru='Специальное'),
    EDUCATION=dict(en='Education', ru='Обучение'),
    DATABASES=dict(en='Databases', ru='Базы данных'),
    MULTIMEDIA=dict(en='Multimedia', ru='Мультимедиа'),
    MOBILE=dict(en='Mobile', ru='Мобильные'),
    SECURITY=dict(en='Security', ru='Безопасность'),
    SYSADM=dict(en='System Administration', ru='Системное администрирование'),
    DEVOPS=dict(en='DevOps', ru='DevOps'),
    DATA_SCIENCE=dict(en='AI & Data Science', ru='AI & Data Science'),
    WEB=dict(en='Web', ru='Web'),
    DEV=dict(en='Development', ru='Для разработчиков'),
    TESTING=dict(en='Testing', ru='Тестирование'),
    HISTORY=dict(en='History', ru='История'),
    MANAGEMENT=dict(en='Management', ru='Менеджмент'),
    USER=dict(en='User', ru='Пользовательское'),
    GAMES=dict(en='Games', ru='Игры'),
    HARDWARE=dict(en='Hardware', ru='Железо'),
    MISC=dict(en='Misc', ru='Разное'),
)

# Logger
log = getLogger(__name__.split('.')[-1])


class TimeoutHTTPAdapter(HTTPAdapter):
    """HTTP adapter with timeout and retries"""

    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        kwargs['max_retries'] = Retry(
            backoff_factor=1,
            total=kwargs.get('max_retries', DEFAULT_RETRIES),
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=['OPTIONS', 'HEAD', 'GET'],
        )
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs['timeout'] = self.timeout
        return super().send(request, **kwargs)


class BotUser:
    """FOSS News Telegram Bot user"""

    def __init__(self, user: User, id_: int = None, groups: list = None) -> None:
        self.id = id_
        self.tid = user.id

        if user.username:
            self.name = user.username
        else:
            self.name = user.first_name
            if user.last_name:
                self.name += ' ' + user.last_name

        self.lang = user.language_code if user.language_code and user.language_code in LANGUAGES else 'en'
        self.groups = groups if groups is not None else DEFAULT_GROUPS

    def __str__(self) -> str:
        _id = str(self.tid)
        if self.id:
            _id += '|' + str(self.id)
        return f'{self.name} ({_id})'

    def is_admin(self) -> bool:
        return 'admins' in self.groups

    def is_editor(self) -> bool:
        return 'editors' in self.groups or self.is_admin()


class cached_user_method:
    """Users caching decorator"""

    def __init__(self, maxsize: int = 128, days: float = 0, seconds: float = 0, microseconds: float = 0,
                 milliseconds: float = 0, minutes: float = 0, hours: float = 0, weeks: float = 0) -> None:
        self.cache = LRUCacheTTL(maxsize=maxsize, days=days, seconds=seconds, microseconds=microseconds,
                                 milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)

    def __call__(self, fetch: Callable[[Any, User], BotUser]) -> Callable[[Any, User], BotUser]:
        @wraps(fetch)
        def wrapper(obj: Any, user: User) -> BotUser:
            try:
                return self.cache[user.id]
            except KeyError:
                pass

            value = fetch(obj, user)
            self.cache[user.id] = value

            return value

        wrapper.cache_info = self.cache.info

        return wrapper


class FNGS:
    """FOSS News Gathering Server API"""

    def __init__(self, endpoint: str, username: str, password: str,
                 timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_RETRIES):
        self._endpoint = endpoint
        self._auth = dict(username=username, password=password)
        self._headers = {}
        self._http = BaseUrlSession(endpoint)
        self._adapter = TimeoutHTTPAdapter(timeout=timeout, max_retries=max_retries)
        self._http.mount('https://', self._adapter)
        self._http.mount('http://', self._adapter)

    @cached_property_with_ttl(days=config.cache.token.ttl)
    def token(self):
        """Fetch FNGS token"""
        t = self._http.post('token/', data=self._auth).json()['access']
        log.info('fetched token')
        return t

    @property
    def headers(self) -> dict:
        self._headers['Authorization'] = f'Bearer {self.token}'
        return self._headers

    def _request(self, endpoint: str, method: str, query: dict = None, data: dict = None) -> Optional[Response]:
        url, response = f'{endpoint}/', None

        if query:
            url += '?' + urlencode(query, doseq=True)
        log.debug('request: %s %s data=%s', method.upper(), url, data)

        if method == 'get':
            response = self._http.get(url, headers=self.headers)
        elif method == 'post':
            response = self._http.post(url, headers=self.headers, data=data)
        elif method == 'patch':
            response = self._http.patch(url, headers=self.headers, data=data)

        if response is not None:
            response.raise_for_status()

        return response

    @cached_property_with_ttl(days=config.cache.attrs.ttl)
    def types(self) -> dict:
        """Fetch types of news"""
        # TODO: replace test types data with a real request
        # t = self.request('telegram-bot-types', 'get').json()
        t = TEST_TYPES
        log.info('fetched news types')
        return t

    @cached_property_with_ttl(days=config.cache.attrs.ttl)
    def categories(self) -> dict:
        """Fetch categories of news"""
        # TODO: replace test categories data with a real request
        # c = self.request('telegram-bot-categories', 'get').json()
        c = TEST_CATEGORIES
        log.info('fetched news categories')
        return c

    def register_user(self, user: User) -> Optional[int]:
        """Register Telegram user on FNGS server"""
        user = BotUser(user)
        try:
            user.id = self._request('telegram-bot-user', 'post',
                                    data=dict(tid=user.tid, username=user.name)).json()['id']
            log.info("%s was registered successfully", user)
            return user.id
        except HTTPError as e:
            r = e.response
            if r.status_code == 400:  # TODO: make error code more specific
                log.warning("%s was already registered: %s", user, r.json()['tid'][0])
                return None
            else:
                raise e

    @cached_user_method(days=config.cache.users.ttl, maxsize=config.cache.users.size)
    def fetch_user(self, user: User) -> BotUser:
        """Fetch FNGS id and info for Telegram user"""

        def _fetch(tid: int) -> Any:
            return self._request('telegram-bot-user-by-tid', 'get', query=dict(tid=tid)).json()

        try:
            user_info = _fetch(user.id)
        except HTTPError as e:
            r = e.response
            if r.status_code == 404:
                self.register_user(user)
                user_info = _fetch(user.id)
            else:
                raise e

        try:
            groups = [g['name'] for g in user_info['groups']]
        except KeyError:
            groups = None
        user = BotUser(user, user_info['id'], groups)
        log.info("%s was fetched", user)

        return user

    def update_user_news_lang(self, user: Union[User, BotUser], lang: str) -> None:
        if isinstance(user, User):
            user = self.fetch_user(user)
        raise NotImplementedError('implement `news_lang` field in `telegram-bot-user` model')
        # self._request('telegram-bot-user', 'patch', data=dict(id=user.id, news_lang=lang))

    def fetch_news(self, user: Union[User, BotUser]) -> dict:
        """Fetch next random uncategorized news for this user"""
        if isinstance(user, User):
            user = self.fetch_user(user)

        try:
            news = self._request('telegram-bot-one-random-not-categorized-foss-news-digest-record', 'get',
                                 query={'tbot-user-id': user.id}).json()['results'][0]
            log.info("%s fetched news: id=%i \"%s\"", user, news['id'], news['title'])
        except (JSONDecodeError, IndexError):
            news = {}
            log.warning("%s has no news", user)

        return news

    def fetch_news_count(self, user: Union[User, BotUser]) -> int:
        """Fetch count of uncategorized news for this user"""
        if isinstance(user, User):
            user = self.fetch_user(user)

        count = self._request('telegram-bot-not-categorized-foss-news-digest-records-count', 'get',
                              query={'tbot-user-id': user.id}).json()['count']
        log.info("%s fetched news count: %i", user, count)

        return count

    def send_attempt(self, user: Union[User, BotUser], news_id: int, state: str = None) -> int:
        """Send categorization attempt of this user"""
        if isinstance(user, User):
            user = self.fetch_user(user)

        if config.env == 'production':
            r = self._request('telegram-bot-digest-record-categorization-attempt', 'post', data=dict(
                dt=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z'),
                telegram_bot_user=user.id,
                digest_record=news_id,
                estimated_state=state,
            ))
            attempt_id = r.json()['id']
        else:
            attempt_id = randint(0, 255)
        log.info("%s sent attempt: id=%i news=%i state=%s", user, attempt_id, news_id, state)

        return attempt_id

    def update_attempt(self, user: Union[User, BotUser], attempt_id: int, field: str, value: Union[bool, int, str]) -> None:
        """Update categorization attempt of this user"""
        if isinstance(user, User):
            user = self.fetch_user(user)

        if config.env == 'production':
            self._request(f'telegram-bot-digest-record-categorization-attempt/{attempt_id}', 'patch',
                          data={field: value})
        log.info("%s updated attempt: id=%i %s=%s", user, attempt_id, field, value)
