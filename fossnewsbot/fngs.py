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

from datetime import datetime, timedelta
from json import JSONDecodeError
import logging
from typing import Optional, Union
from urllib.parse import urlencode

from aiogram.types import User
import requests

from config import config
from cache import TimedProperty
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

log = logging.getLogger('fngs')


class Fngs:
    def __init__(self, endpoint: str, username: str, password: str):
        self._endpoint = endpoint
        self._auth = dict(username=username, password=password)

    @TimedProperty(timedelta(days=config.timeout.token))
    def token(self):
        """Get FNGS token"""
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

    @TimedProperty(timedelta(days=config.timeout.cache))
    def types(self) -> dict:
        """Get types of news"""
        # TODO: replace test types data with a real request
        # t = self.request('telegram-bot-types', 'get').json()
        t = TEST_TYPES
        log.info('fetched types')
        return t

    @TimedProperty(timedelta(days=config.timeout.cache))
    def categories(self) -> dict:
        """Get categories of news"""
        # TODO: replace test categories data with a real request
        # c = self.request('telegram-bot-categories', 'get').json()
        c = TEST_CATEGORIES
        log.info('fetched categories')
        return c

    def register_user(self, user: User) -> Optional[int]:
        """Register Telegram user on FNGS server"""
        tid, username = user.id, get_username(user)

        try:
            user_id = self._request('telegram-bot-user', 'post', data=dict(tid=tid, username=username)).json()['id']
            log.info("user '%s' tid=%i id=%i: registered successfully", username, tid, user_id)
            return user_id
        except requests.HTTPError as e:
            r = e.response
            if r.status_code == 400:
                log.warning("user '%s' tid=%i: already registered: %s", username, tid, r.json()['tid'][0])
                return None
            else:
                raise e

    def fetch_user(self, user: User) -> int:
        """Get FNGS id of Telegram user"""
        tid, username = user.id, get_username(user)

        user_id = self._request('telegram-bot-user-by-tid', 'get', query=dict(tid=tid)).json()['id']
        log.info("user '%s' tid=%i id=%i", username, tid, user_id)

        return user_id

    def fetch_news(self, user: User) -> dict:
        """Get next random news"""
        tid, username = user.id, get_username(user)

        try:
            user_id = self.fetch_user(user)
        except (requests.HTTPError, JSONDecodeError, KeyError):
            user_id = self.register_user(user)

        try:
            news = self._request('telegram-bot-one-random-not-categorized-foss-news-digest-record', 'get',
                                 query={'tbot-user-id': user_id}).json()[0]
            log.info("user '%s' tid=%i id=%i: fetched news=%i title=\"%s\"",
                     username, tid, user_id, news['id'], news['title'])
        except (JSONDecodeError, IndexError):
            news = {}
            log.info("user '%s' tid=%i id=%i: no news", username, tid, user_id)

        return news

    def send_attempt(self, user: User, news_id: int, state: str = None) -> int:
        """Send current categorization attempt"""
        tid, username = user.id, get_username(user)
        user_id = self.fetch_user(user)

        if config.env == 'production':
            r = self._request('telegram-bot-digest-record-categorization-attempt', 'post', data=dict(
                dt=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z'),
                telegram_bot_user=user_id,
                digest_record=news_id,
                estimated_state=state,
            ))
            attempt_id = r.json()['id']
        else:
            attempt_id = 42
        log.info("user '%s' tid=%i id=%i: sent attempt id=%i news=%i state=%s",
                 username, tid, user_id, attempt_id, news_id, state)

        return attempt_id

    def update_attempt(self, user: User, attempt_id: int, field: str, value: Union[bool, int, str]) -> None:
        """Update current categorization attempt"""
        tid, username = user.id, get_username(user)
        user_id = self.fetch_user(user)

        if config.env == 'production':
            self._request('telegram-bot-digest-record-categorization-attempt', 'patch',
                          data={'id': attempt_id, field: value})
        log.info("user '%s' tid=%i id=%i: updated attempt id=%i %s=%s",
                 username, tid, user_id, attempt_id, field, value)
