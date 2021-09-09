"""Cached property with timeout"""

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

from datetime import datetime, timedelta
from typing import Any, Callable, Optional


class TimedProperty:
    """Decorator for cached property with timeout"""
    def __init__(self, timeout: timedelta):
        self._timeout: timedelta = timeout
        self._updated_at: Optional[datetime] = None
        self._update: Optional[Callable[[Any], Any]] = None
        self._value: Optional[Any] = None

    def __call__(self, update: Callable[[Any], Any]):
        self.__doc__ = update.__doc__
        self._update = update

        return self

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if obj is None or self._update is None:
            return self

        now = datetime.utcnow()
        if not self._value or (self._timeout and self._updated_at and now - self._updated_at >= self._timeout):
            self._value = self._update(obj)
            self._updated_at = now

        return self._value
