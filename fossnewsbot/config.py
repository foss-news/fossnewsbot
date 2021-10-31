"""FOSS News Telegram Bot settings"""

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

from dynaconf import Dynaconf, Validator


PREFIX = 'FOSSNEWSBOT'

config = Dynaconf(
    envvar_prefix=PREFIX,
    envvar=f'{PREFIX}_CONFIG',
    env_switcher=f'{PREFIX}_ENV',
    environments=True,
    settings_files=['config.yml', '.secrets.yml'],
    validators=[
        Validator('bot.token', 'fngs.username', 'fngs.username', required=True),
        Validator('bot.host', default='127.0.0.1'),
        Validator('bot.port', default=2048, is_type_of=int),
        Validator('webhook.base', default='https://fn.permlug.org', is_type_of=str, startswith='http'),
        Validator('webhook.path', default='/bot/', is_type_of=str, startswith='/'),
        Validator('fngs.endpoint', default='https://fn.permlug.org/api/v1/', is_type_of=str, startswith='http'),
        Validator('fngs.timeout', default=5, is_type_of=int),
        Validator('fngs.retries', default=3, is_type_of=int),
        Validator('log.level', default='info'),
        Validator('localedir', default='locales'),
        Validator('url.channel', default='https://t.me/permlug', is_type_of=str, startswith='http'),
        Validator('url.chat', default='https://t.me/permlug_chat', is_type_of=str, startswith='http'),
        Validator('marker.count', default='📊'),
        Validator('marker.date', default='🗓'),
        Validator('marker.lang', default='🌏'),
        Validator('marker.keywords.title', default='🏷'),
        Validator('marker.keywords.foss', default='🟢'),
        Validator('marker.keywords.proprietary', default='🟡'),
        Validator('marker.content_type', default='🔖'),
        Validator('marker.content_category', default='🗂'),
        Validator('marker.include', default='✅'),
        Validator('marker.exclude', default='⛔️'),
        Validator('marker.unknown', default='🤷🏻‍♂️'),
        Validator('marker.is_main', default='❗️'),
        Validator('marker.short', default='📃'),
        Validator('marker.error', default='🤔'),
        Validator('keyboard.columns', default=3, is_type_of=int),
        Validator('cache.token.ttl', default=29, is_type_of=int),
        Validator('cache.attrs.ttl', default=1, is_type_of=int),
        Validator('cache.users.ttl', default=1, is_type_of=int),
        Validator('cache.users.size', default=256, is_type_of=int),
        Validator('features.is_main', default=False, is_type_of=bool),
        Validator('features.types', default=False, is_type_of=bool),
        Validator('features.categories', default=False, is_type_of=bool),
    ],
)
