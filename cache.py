"""Cache control"""

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
from functools import update_wrapper
from typing import Any, Callable


class CachedProperty:
    """Decorator for cached property with TTL"""

    def __init__(self, days: float = 0, seconds: float = 0, microseconds: float = 0, milliseconds: float = 0,
                 minutes: float = 0, hours: float = 0, weeks: float = 0):
        self.__ttl__ = timedelta(days=days, seconds=seconds, microseconds=microseconds,
                                 milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)
        self.__dt__ = None
        self.__wrapped__ = None

    def __call__(self, fget: Callable[[Any], Any]) -> Any:
        update_wrapper(self, fget)
        return self

    def __get__(self, obj: Any, cls: Any = None) -> Any:
        if obj is None or self.__wrapped__ is None:
            return self

        now = datetime.utcnow()
        try:
            if self.__ttl__ and self.__dt__ and now - self.__dt__ >= self.__ttl__:
                raise AttributeError
            return obj.__dict__[self.__name__]
        except (AttributeError, KeyError):
            self.__dt__ = now
            obj.__dict__[self.__name__] = self.__wrapped__(obj)
            return obj.__dict__[self.__name__]

    def __delete__(self, obj: Any) -> None:
        try:
            del obj.__dict__[self.__name__]
        except KeyError:
            pass
