"""Run FOSS News Telegram Bot"""

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

import logging
import random
import sys

from aiogram import executor
from requests import RequestException

from . import log, fngs, dispatcher, handlers
from .config import config


LOG_LEVELS = dict(
    debug=logging.DEBUG,
    info=logging.INFO,
    warn=logging.WARNING,
    warning=logging.WARNING,
    error=logging.ERROR,
    critical=logging.CRITICAL,
)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(name)s - %(message)s',
        level=LOG_LEVELS.get(config.get('log.level', 'info'), logging.INFO),
    )

    try:
        token = fngs.token
    except RequestException as ex:
        log.critical('Cannot fetch FNGS token: %s', ex)
        sys.exit(1)

    if config.env != 'production':
        random.seed()

    executor.start_polling(dispatcher, timeout=60, skip_updates=True)
