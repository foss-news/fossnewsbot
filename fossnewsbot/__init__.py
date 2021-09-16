"""FOSS News Telegram Bot

fossnewsbot sends you news collected for the next digest one by one to filter and categorize.
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

from logging import getLogger

from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode

from .config import config
from .fngs import Fngs


log = getLogger(__name__)
bot = Bot(token=config.bot.token, parse_mode=ParseMode.MARKDOWN_V2)
dispatcher = Dispatcher(bot)
fngs = Fngs(config.fngs.endpoint, config.fngs.username, config.fngs.password)
