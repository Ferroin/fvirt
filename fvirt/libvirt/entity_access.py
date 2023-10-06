# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Classes used by fvirt.libvirt.Hypervisor instances for entity access.'''

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping, Sized
from typing import TYPE_CHECKING, Any, Self, cast
from uuid import UUID

from .entity import ConfigurableEntity, Entity

if TYPE_CHECKING:
    import re

    from .hypervisor import Hypervisor
    from ..util.match import MatchTarget


class BaseEntityAccess(ABC, Sized):
    '''Abstract base class for entity access protocols.'''
    def __init__(self: Self, parent: Hypervisor | Entity) -> None:
        self._parent = parent

    def __repr__(self: Self) -> str:
        return f'<fvirt.libvirt.{ type(self).__name__ }: { repr(self._parent) }>'

    def __len__(self: Self) -> int:
        total = 0

        with self._parent:
            link = self._get_parent_link()

            for func in self._count_funcs:
                total += cast(int, getattr(link, func)())

        return total

    def _get_parent_link(self: Self) -> Any:
        if hasattr(self._parent, '_connection'):
            link = self._parent
            assert link._connection is not None
            return link._connection
        else:
            link = self._parent._entity
            assert link is not None
            return link

    @property
    @abstractmethod
    def _count_funcs(self: Self) -> Iterable[str]:
        '''An iterable of methods to call to get counts of the entities.

           This usually should be the pair of `numOf` and `numOfDefined`
           methods corresponding to the type of entity.'''

    @property
    @abstractmethod
    def _list_func(self: Self) -> str:
        '''The name of the function used to list all of the entities.'''

    @property
    @abstractmethod
    def _entity_class(self: Self) -> type:
        '''The class used to encapsulate the entities.'''


class EntityMap(BaseEntityAccess, Mapping):
    '''ABC for mappings of entities on a hypervisor.'''
    def __iter__(self: Self) -> Iterator[str]:
        with self._parent:
            link = self._get_parent_link()

            match getattr(link, self._list_func)():
                case None:
                    return iter([])
                case entities:
                    return iter([x.name() for x in entities])

    def __getitem__(self: Self, key: Any) -> Entity:
        key = self._coerce_key(key)

        with self._parent:
            link = self._get_parent_link()

            match getattr(link, self._lookup_func)(key):
                case None:
                    raise KeyError(key)
                case entity:
                    return cast(Entity, self._entity_class(entity, self._parent))

    @abstractmethod
    def _get_key(self: Self, entity: Any) -> Any:
        '''Get the key for a given entity.'''

    @abstractmethod
    def _coerce_key(self: Self, key: Any) -> Any:
        '''Method used to coerce keys to the type expected by the lookup method.'''

    @property
    @abstractmethod
    def _lookup_func(self: Self) -> str:
        '''Name of the lookup method called on virConnect to find an entity.'''


class NameMap(EntityMap):
    '''Mapping access to entities by name.'''
    def _get_key(self: Self, entity: Any) -> str:
        return cast(str, entity.name())

    def _coerce_key(self: Self, key: Any) -> str:
        if not isinstance(key, str):
            raise KeyError(key)

        return key


class UUIDMap(EntityMap):
    '''Mapping access by UUID.

       On access, accepts either a UUID string, a big-endian bytes object
       representing the raw bytes of the UUID, or a pre-constructed
       UUID object. Strings and bytes are parsed as UUIDs using the uuid.UUID
       class from the Python standard library, with keys that evaulate
       to an equivalent uuid.UUID object being treated as identical.

       If a string or bytes object is used as a key and it cannot be
       converted to a UUID object, a ValueError will be raised.

       When iterating keys, only uuid.UUID objects will be returned.'''
    def _get_key(self: Self, entity: Any) -> UUID:
        return UUID(entity.uuidString())

    def _coerce_key(self: Self, key: Any) -> str:
        match key:
            case str():
                pass
            case bytes():
                key = str(UUID(bytes=key))
            case UUID():
                key = str(key)
            case _:
                raise KeyError(key)

        return cast(str, key)


class EntityAccess(BaseEntityAccess, Iterable):
    '''Class providing top-level entity access protocol.

       Instances are directly iterable to access entities, though the
       iteration order is explicitly not specified.

       When used as an iterator, the underlying libvirt objects are all
       allocated when initially starting iteration, but the fvirt.libvirt
       wrappers are only constructed as needed. This saves some memory
       for the common case of the individual objects going out of scope
       relatively quickly, but it also means that iterator access only
       works correctly if you have something holding the Hypervisor
       connection open.'''
    def __iter__(self: Self) -> Iterator[Entity]:
        with self._parent:
            link = self._get_parent_link()

            match getattr(link, self._list_func)():
                case None:
                    return iter([])
                case entities:
                    return iter(self._entity_class(x, self._parent) for x in entities)

    def get(self: Self, key: str) -> Entity | None:
        '''Look up an entity by a general identifier.

           This tries, in order, looking up by name and then by UUID. If
           it can't find an entity based on that key, it returns None.'''
        ret: Entity | None = None

        if hasattr(self, 'by_name'):
            ret = self.by_name.get(key, None)

        if ret is None and hasattr(self, 'by_uuid'):
            try:
                uuid = UUID(key)
            except ValueError:
                pass
            else:
                ret = self.by_uuid.get(uuid, None)

        return ret

    def match(self: Self, match: tuple[MatchTarget, re.Pattern]) -> Iterable[ConfigurableEntity]:
        '''Return an iterable of entities that match given match parameters.'''
        def f(entity: ConfigurableEntity) -> bool:
            value = match[0].get_value(entity)
            return match[1].match(value) is not None

        return filter(f, self)
