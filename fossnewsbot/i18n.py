"""Internationalization of FOSS News Telegram Bot"""

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

from gettext import translation  # Do not import gettext as `_` explicitly! See comment below.
import locale
import logging

from aiogram.types import User

from config import config


LANGUAGES = ['en', 'ru']
TEXTDOMAIN = 'fossnewsbot'

translations = {lang: translation(TEXTDOMAIN, localedir=config.localedir, languages=[lang]) for lang in LANGUAGES}
# Function `_` is added to the global namespace by method `install`.
# Do not define or import `_` as an alias for `gettext`!
translations['en'].install()

log = logging.getLogger(__name__)


def get_language(user: User) -> str:
    lang = user.locale.language
    if lang not in LANGUAGES:
        lang = 'en'

    return lang


def set_language(lang: str) -> None:
    try:
        locale.setlocale(locale.LC_ALL, lang)
    except locale.Error as e:
        log.warning("Cannot set locale '%s': %s", lang, e)
    translations.get(lang, translations['en']).install()
