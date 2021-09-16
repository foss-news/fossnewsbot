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
from functools import lru_cache
from json import JSONDecodeError
from logging import getLogger
from random import randint
from typing import Optional, Tuple, Union
from urllib.parse import urlencode

import requests
from aiogram.types import User

from cache import CachedProperty
from .config import config
from .tg_user import get_username


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

log = getLogger('fngs')


class Fngs:
    def __init__(self, endpoint: str, username: str, password: str):
        self._endpoint = endpoint
        self._auth = dict(username=username, password=password)

    @CachedProperty(days=config.cache.token.ttl)
    def token(self):
        """Fetch FNGS token"""
        t = requests.post(self._endpoint + 'token/', data=self._auth).json()['access']
        log.info('fetched token')
        return t

    def _request(self, endpoint: str, method: str, query: dict = None, data: dict = None) -> Optional[requests.Response]:
        url, response = f'{self._endpoint}{endpoint}/', None
        headers = dict(Authorization=f'Bearer {self.token}')

        if query:
            url += '?' + urlencode(query, doseq=True)
        log.debug('request: %s %s data=%s', method.upper(), url, data)

        if method == 'get':
            response = requests.get(url, headers=headers)
        elif method == 'post':
            response = requests.post(url, headers=headers, data=data)
        elif method == 'patch':
            response = requests.patch(url, headers=headers, data=data)

        if response is not None:
            response.raise_for_status()

        return response

    @CachedProperty(days=config.cache.attrs.ttl)
    def types(self) -> dict:
        """Fetch types of news"""
        # TODO: replace test types data with a real request
        # t = self.request('telegram-bot-types', 'get').json()
        t = TEST_TYPES
        log.info('fetched news types')
        return t

    @CachedProperty(days=config.cache.attrs.ttl)
    def categories(self) -> dict:
        """Fetch categories of news"""
        # TODO: replace test categories data with a real request
        # c = self.request('telegram-bot-categories', 'get').json()
        c = TEST_CATEGORIES
        log.info('fetched news categories')
        return c

    def register_user(self, user: User) -> Optional[int]:
        """Register Telegram user on FNGS server"""
        tid, username = user.id, get_username(user)

        try:
            user_id = self._request('telegram-bot-user', 'post', data=dict(tid=tid, username=username)).json()['id']
            log.info("%s (%i|%i) registered successfully", username, tid, user_id)
            return user_id
        except requests.HTTPError as e:
            r = e.response
            if r.status_code == 400:
                log.warning("%s (%i) already registered: %s", username, tid, r.json()['tid'][0])
                return None
            else:
                raise e

    @lru_cache(maxsize=config.cache.users.size)
    def fetch_user(self, user: User) -> Tuple[str, int, int]:
        """Fetch FNGS id of Telegram user"""
        tid, username = user.id, get_username(user)

        try:
            user_id = self._request('telegram-bot-user-by-tid', 'get', query=dict(tid=tid)).json()['id']
        except (requests.HTTPError, JSONDecodeError, KeyError):
            user_id = self.register_user(user)
        log.info("%s (%i|%i) fetched id", username, tid, user_id)

        return username, tid, user_id

    def fetch_news(self, user: User) -> dict:
        """Fetch next random uncategorized news for this user"""
        username, tid, user_id = self.fetch_user(user)

        try:
            news = self._request('telegram-bot-one-random-not-categorized-foss-news-digest-record', 'get',
                                 query={'tbot-user-id': user_id}).json()[0]
            log.info("%s (%i|%i) fetched news %i \"%s\"", username, tid, user_id, news['id'], news['title'])
        except (JSONDecodeError, IndexError):
            news = {}
            log.warning("%s (%i|%i) got no news", username, tid, user_id)

        return news

    def fetch_news_count(self, user: User) -> int:
        """Fetch count of uncategorized news for this user"""
        username, tid, user_id = self.fetch_user(user)

        count = self._request('telegram-bot-not-categorized-foss-news-digest-records-count', 'get',
                              query={'tbot-user-id': user_id}).json()['count']
        log.info("%s (%i|%i) fetched news count %i", username, tid, user_id, count)

        return count

    def send_attempt(self, user: User, news_id: int, state: str = None) -> int:
        """Send categorization attempt of this user"""
        username, tid, user_id = self.fetch_user(user)

        if config.env == 'production':
            r = self._request('telegram-bot-digest-record-categorization-attempt', 'post', data=dict(
                dt=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z'),
                telegram_bot_user=user_id,
                digest_record=news_id,
                estimated_state=state,
            ))
            attempt_id = r.json()['id']
        else:
            attempt_id = randint(0, 255)
        log.info("%s (%i|%i) sent attempt %i news=%i state=%s", username, tid, user_id, attempt_id, news_id, state)

        return attempt_id

    def update_attempt(self, user: User, attempt_id: int, field: str, value: Union[bool, int, str]) -> None:
        """Update categorization attempt of this user"""
        username, tid, user_id = self.fetch_user(user)

        if config.env == 'production':
            self._request('telegram-bot-digest-record-categorization-attempt', 'patch',
                          data={'id': attempt_id, field: value})
        log.info("%s (%i|%i) updated attempt %i %s=%s", username, tid, user_id, attempt_id, field, value)
