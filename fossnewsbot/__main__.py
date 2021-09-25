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

from . import log, fngs, dispatcher, bot
from .config import config


LOG_LEVELS = dict(
    debug=logging.DEBUG,
    info=logging.INFO,
    warn=logging.WARNING,
    warning=logging.WARNING,
    error=logging.ERROR,
    critical=logging.CRITICAL,
)

WEBHOOK_HOST = "https://fn.permlug.org"
WEBHOOK_PATH = "/webhook/"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "127.0.0.1"
WEBAPP_PORT = 3000


async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)


# Run before shutdown
async def on_shutdown(dp):
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")

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

    # executor.start_polling(dispatcher, timeout=60, skip_updates=True)
    executor.start_webhook(
        dispatcher=dispatcher,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        )

