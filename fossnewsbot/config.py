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
        Validator('bot.token', 'fngs.username', 'fngs.username', must_exist=True),
        Validator('fngs.endpoint', default='https://fn.permlug.org/api/v1/'),
        Validator('log.level', default='info'),
        Validator('localedir', default='locales'),
        Validator('url.channel', default='https://t.me/permlug'),
        Validator('url.chat', default='https://t.me/permlug_chat'),
        Validator('marker.date', default='🗓'),
        Validator('marker.lang', default='🌏'),
        Validator('marker.keywords', default='🏷'),
        Validator('marker.type', default='🔖'),
        Validator('marker.category', default='🗂'),
        Validator('marker.include', default='✅'),
        Validator('marker.exclude', default='⛔️'),
        Validator('marker.unknown', default='🤷🏻‍♂️'),
        Validator('marker.is_main', default='❗️'),
        Validator('marker.short', default='📃'),
        Validator('marker.error', default='🤔'),
        Validator('keyboard.columns', default=3),
        Validator('cache.token.ttl', default=29),
        Validator('cache.attrs.ttl', default=1),
        Validator('cache.users.size', default=256),
        Validator('features.is_main', default=False),
        Validator('features.types', default=False),
        Validator('features.categories', default=False),
    ],
)
