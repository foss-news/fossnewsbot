"""Caching"""

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

from collections import Mapping, namedtuple
from datetime import datetime, timedelta
from functools import update_wrapper
from typing import Any, Callable, Generator, Tuple


CacheInfoTTL = namedtuple('CacheInfo', ['hits', 'misses', 'maxsize', 'currsize', 'ttl'])


class cached_property_with_ttl:
    """Decorator for cached property with TTL"""

    def __init__(self, days: float = 0, seconds: float = 0, microseconds: float = 0, milliseconds: float = 0,
                 minutes: float = 0, hours: float = 0, weeks: float = 0):
        self._ttl = timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds,
                              minutes=minutes, hours=hours, weeks=weeks)
        self._dt = None
        self._hits = 0
        self._misses = 0
        self.__wrapped__ = None

    def __call__(self, fget: Callable[[Any], Any]) -> Any:
        update_wrapper(self, fget)
        return self

    def __get__(self, obj: Any, cls: Any = None) -> Any:
        if obj is None or self.__wrapped__ is None:
            return self

        try:
            if self._ttl and self._dt and datetime.utcnow() - self._dt >= self._ttl:
                raise AttributeError
            value = obj.__dict__[self.__name__]
            self._hits += 1
        except (AttributeError, KeyError):
            value = self.__wrapped__(obj)
            obj.__dict__[self.__name__] = value
            self._dt = datetime.utcnow()
            self._misses += 1

        return value

    def __delete__(self, obj: Any) -> None:
        try:
            del obj.__dict__[self.__name__]
        except KeyError:
            pass

    def info(self) -> CacheInfoTTL:
        return CacheInfoTTL(hits=self._hits, misses=self._misses, maxsize=1, currsize=1, ttl=self._ttl)


class CacheNode:
    """Node in doubly linked list and hash map"""

    __slots__ = ('empty', 'next', 'prev', 'key', 'value', 'dt')

    def __init__(self) -> None:
        self.empty = True
        self.key = None
        self.value = None
        self.dt = None

    def __str__(self) -> str:
        return f'{self.key}: {self.value}'

    def __bool__(self) -> bool:
        return not self.empty

    def set(self, key: Any, value: Any) -> None:
        self.empty = False
        self.key = key
        self.value = value
        self.dt = datetime.utcnow()

    def clear(self) -> None:
        self.__init__()


class LRUCacheTTL:
    """LRU cache with TTL"""

    def __init__(self, maxsize: int = 128, days: float = 0, seconds: float = 0, microseconds: float = 0,
                 milliseconds: float = 0, minutes: float = 0, hours: float = 0, weeks: float = 0) -> None:
        self._data = {}
        self._head = CacheNode()
        self._head.next = self._head
        self._head.prev = self._head
        self._maxsize = 1
        self.maxsize = maxsize
        self._ttl = timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds,
                              minutes=minutes, hours=hours, weeks=weeks)
        self.hits = 0
        self.misses = 0

    def __str__(self) -> str:
        return '{' + ', '.join([str(node) for node in self._iter()]) + '}'

    def __bool__(self) -> bool:
        return bool(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def _move_to_tail(self, node: CacheNode) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = self._head.prev
        node.next = self._head.prev.next
        node.next.prev = node
        node.prev.next = node

    def peek(self, key: Any) -> Any:
        return self._data[key].value

    def __getitem__(self, key):
        try:
            node = self._data[key]
        except KeyError as ex:
            self.misses += 1
            raise ex

        if datetime.utcnow() - node.dt >= self._ttl:
            if self._head == node:
                self._head = node.next
            else:
                self._move_to_tail(node)
            del self[key]
            self.misses += 1
            raise KeyError(key)

        self._move_to_tail(node)
        self._head = node
        self.hits += 1

        return node.value

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Any, value: Any) -> None:
        if key in self._data:
            node = self._data[key]
            node.value = value
            self._move_to_tail(node)
            self._head = node
            return

        node = self._head.prev
        if node:
            del self._data[node.key]
        node.set(key, value)
        self._data[key] = node
        self._head = node

    def setdefault(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def __delitem__(self, key):
        node = self._data[key]
        del self._data[key]
        node.clear()
        self._move_to_tail(node)
        self._head = node.next

    def __contains__(self, key: Any) -> bool:
        return key in self._data

    def _iter(self) -> Generator[CacheNode, None, None]:
        node = self._head
        for i in range(len(self._data)):
            yield node
            node = node.next

    def __iter__(self) -> Generator[Any, None, None]:
        return self.keys()

    def keys(self) -> Generator[Any, None, None]:
        for node in self._iter():
            yield node.key

    def values(self) -> Generator[Any, None, None]:
        for node in self._iter():
            yield node.value

    def items(self) -> Generator[Tuple[Any, Any], None, None]:
        for node in self._iter():
            yield node.key, node.value

    _default = object()

    def pop(self, key: Any, default: Any = _default) -> Any:
        if key in self._data:
            value = self.peek(key)
            del self[key]
            return value

        if default is self._default:
            raise KeyError(key)

        return default

    def popitem(self) -> Tuple[Any, Any]:
        if len(self) < 1:
            raise KeyError

        key = self._head.key
        value = self._head.value
        del self[key]

        return key, value

    def update(self, *args, **kwargs) -> None:
        if len(args) > 0:
            other = args[0]
            if isinstance(other, Mapping):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, 'keys'):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def __ior__(self, other: Any) -> None:
        self.update(other)

    def clear(self) -> None:
        for node in self._iter():
            node.clear()
        self._data.clear()

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @maxsize.setter
    def maxsize(self, size: int) -> None:
        assert size > 0
        n = size - self._maxsize
        if n > 0:
            for i in range(n):
                node = CacheNode()
                node.next = self._head
                node.prev = self._head.prev
                self._head.prev.next = node
                self._head.prev = node
        elif n < 0:
            for i in range(-n):
                node = self._head.prev
                if node:
                    del self._data[node.key]
                self._head.prev = node.prev
                node.prev.next = self._head
                node.clear()
                node.next = node.prev = None
        self._maxsize += n

    def info(self) -> CacheInfoTTL:
        return CacheInfoTTL(hits=self.hits, misses=self.misses, maxsize=self.maxsize, currsize=len(self), ttl=self._ttl)
