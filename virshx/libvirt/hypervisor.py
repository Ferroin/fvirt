# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt hypervisor connections.'''

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sized, Mapping
from typing import Self, Any, cast
from types import TracebackType
from uuid import UUID

import libvirt

from .domain import Domain
from .entity import Entity
from .exceptions import NotConnected, InvalidConfig, InsufficientPrivileges
from .storage_pool import StoragePool
from .uri import URI


class Hypervisor:
    '''Basic class encapsulating a hypervisor connection.

       This is a wrapper around a libvirt.virConnect instance that
       provides a bunch of extra convenience functionality, such as a
       proper context manager interface and the ability to list _all_
       domains.

       When converting to a boolean, Hypervisor instances are treated as
       false if they are not connected, and true if they have at least
       one active connection.

       Domains can be accessed via the `domains`, `domains_by_name`,
       `domains_by_id`, or `domains_by_uuid` properties.

       Storage pools can be accessed via the `pools`, `pools_by_name`,
       or `pools_by_uuid` properties.'''
    def __init__(self: Self, hvuri: URI, read_only: bool = False) -> None:
        self._uri = hvuri

        self._connection: libvirt.virConnect | None = None
        self.__read_only = bool(read_only)
        self.__conn_count = 0

        self.__domains = Domains(self)
        self.__domains_by_name = DomainsByName(self)
        self.__domains_by_uuid = DomainsByUUID(self)
        self.__domains_by_id = DomainsByID(self)

        self.__pools = StoragePools(self)
        self.__pools_by_name = StoragePoolsByName(self)
        self.__pools_by_uuid = StoragePoolsByUUID(self)

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.Hypervisor: uri={ str(self.uri) }, ro={ self.read_only }, conns={ self.__conn_count }>'

    def __bool__(self: Self) -> bool:
        return self.__conn_count > 0

    def __del__(self: Self) -> None:
        if self._connection is not None and self.__conn_count > 0:
            self._connection.close()
            self._connection = None

    def __enter__(self: Self) -> Self:
        return self.open()

    def __exit__(self: Self, _exc_type: type | None, _exc_value: BaseException | None, _traceback: TracebackType | None) -> None:
        self.close()

    def __define_entity(self: Self, entity_class: type[Entity], method: str, config: str, flags: int = 0) -> Entity:
        if self.read_only:
            raise InsufficientPrivileges

        if self._connection is None:
            raise NotConnected

        try:
            entity = getattr(self._connection, method)(config, flags)
        except libvirt.LibvirtError:
            raise InvalidConfig

        return entity_class(entity, self)

    @property
    def read_only(self: Self) -> bool:
        return self.__read_only

    @property
    def uri(self: Self) -> URI:
        with self:
            assert self._connection is not None
            return URI.from_string(self._connection.getURI())

    @property
    def domains(self: Self) -> Domains:
        '''Iterator access to all domains defined by the Hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__domains

    @property
    def domains_by_name(self: Self) -> DomainsByName:
        '''Mapping access by name to all domains in the hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__domains_by_name

    @property
    def domains_by_uuid(self: Self) -> DomainsByUUID:
        '''Mapping access by UUID to all domains in the hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__domains_by_uuid

    @property
    def domains_by_id(self: Self) -> DomainsByID:
        '''Mapping access by id to running domains in the hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__domains_by_id

    @property
    def pools(self: Self) -> StoragePools:
        '''Iterator access to all pools defined by the Hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__pools

    @property
    def pools_by_name(self: Self) -> StoragePoolsByName:
        '''Mapping access by name to all storage pools in the hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__pools_by_name

    @property
    def pools_by_uuid(self: Self) -> StoragePoolsByUUID:
        '''Mapping access by UUID to all storage pools in the hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__pools_by_uuid

    def open(self: Self) -> Self:
        '''Open the connection represented by this Hypervisor instance.

           In most cases, it is preferred to use either the context
           manager interface, or property access, both of which will
           handle connections correctly for you.'''
        if self._connection is None:
            try:
                if self.read_only:
                    self._connection = libvirt.openReadOnly(str(self._uri))
                else:
                    self._connection = libvirt.open(str(self._uri))
            except libvirt.libvirtError as e:
                raise e

            self.__conn_count += 1
        else:
            if self.__conn_count == 0:
                raise RuntimeError
            else:
                self.__conn_count += 1

        return self

    def close(self: Self) -> None:
        '''Close any open connection represented by this hypervisor instance.

           Open connections will be cleaned up automatically when a
           Hypervisor instance is destroyed, so you should usually not
           need to call this method directly.'''
        if self._connection is not None and self.__conn_count < 2:
            self._connection.close()
            self._connection = None

        self.__conn_count -= 1

        if self.__conn_count < 0:
            self.__conn_count = 0

    def defineDomain(self: Self, config: str) -> Domain:
        '''Define a domain from an XML config string.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises virshx.libvirt.InvalidConfig if config is not a valid
           libvirt domain configuration.

           Returns a Domain instance for the defined domain on success.'''
        return cast(Domain, self.__define_entity(Domain, 'defineXMLFlags', config, 0))

    def createDomain(self: Self, config: str, paused: bool = False, reset_nvram: bool = False) -> Domain:
        '''Define and start a domain from an XML config string.

           If `paused` is True, the domain will be started in the paused state.

           If `reset_nvram` is True, any existing NVRAM file will be
           reset to a pristine state prior to starting the domain.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises virshx.libvirt.InvalidConfig if config is not a valid
           libvirt domain configuration.

           Returns a Domain instance for the defined domain on success.'''
        flags = 0

        if paused:
            flags |= libvirt.VIR_DOMAIN_START_PAUSED

        if reset_nvram:
            flags |= libvirt.VIR_DOMAIN_START_RESET_NVRAM

        return cast(Domain, self.__define_entity(Domain, 'createXML', config, flags))

    def defineStoragePool(self: Self, config: str) -> StoragePool:
        '''Define a storage pool from an XML config string.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises virshx.libvirt.InvalidConfig if config is not a valid
           libvirt storage pool configuration.

           Returns a StoragePool instance for the defined storage pool on success.'''
        return cast(StoragePool, self.__define_entity(StoragePool, 'storagePoolDefineXML', config, 0))


class HVEntityAccess(ABC, Sized):
    '''Abstract base class for entity access protocols.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'virshx.libvirt.{ type(self).__name__ }: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        total = 0

        for func in self._count_funcs:
            total += cast(int, getattr(self._hv._connection, func)())

        return total

    @property
    @abstractmethod
    def _count_funcs(self: Self) -> Iterable[str]:
        '''An iterable of virConnect methods to call to get counts of the entities.

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


class HVEntityIterator(HVEntityAccess, Iterable):
    '''ABC for entity iterators.'''
    def __iter__(self: Self) -> Iterator[Entity]:
        with self._hv as hv:
            assert hv._connection is not None

            match getattr(hv._connection, self._list_func)():
                case None:
                    return iter([])
                case entities:
                    return iter([self._entity_class(x, hv) for x in entities])


class HVEntityMap(HVEntityAccess, Mapping):
    '''ABC for mappings of entities on a hypervisor.'''
    def __iter__(self: Self) -> Iterator[str]:
        with self._hv as hv:
            assert hv._connection is not None

            match getattr(hv._connection, self._list_func)():
                case None:
                    return iter([])
                case entities:
                    return iter([x.name() for x in entities])

    def __getitem__(self: Self, key: Any) -> Entity:
        key = self._coerce_key(key)

        with self._hv as hv:
            assert hv._connection is not None

            match getattr(hv._connection, self._lookup_func)():
                case None:
                    raise KeyError(key)
                case entity:
                    return cast(Entity, self._entity_class(entity, hv))

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


class HVNameMap(HVEntityMap):
    '''Mapping access by name.'''
    def _get_key(self: Self, entity: Any) -> str:
        return cast(str, entity.name())

    def _coerce_key(self: Self, key: Any) -> str:
        if not isinstance(key, str):
            raise KeyError(key)

        return key


class HVUUIDMap(HVEntityMap):
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


class HVDomainAccess(HVEntityAccess):
    '''Domain access mixin.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfDomains', 'numOfDefinedDomains'}

    @property
    def _list_func(self: Self) -> str:
        return 'listAllDomains'

    @property
    def _entity_class(self: Self) -> type:
        return Domain


class Domains(HVEntityIterator, HVDomainAccess):
    '''Iterator access to domains in a Hypervisor.'''


class DomainsByName(HVNameMap, HVDomainAccess):
    '''A simple mapping of domain names to Domain instances.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByName'


class DomainsByUUID(HVUUIDMap, HVDomainAccess):
    '''A simple mapping of domain UUIDs to Domain instances.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByUUIDString'


class DomainsByID(HVEntityMap, HVDomainAccess):
    '''A simple mapping of domain IDs to Domain instances.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfDomains'}

    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByID'

    def _get_key(self: Self, entity: Any) -> int:
        return cast(int, entity.ID())

    def _coerce_key(self: Self, key: Any) -> int:
        if not isinstance(key, int):
            raise KeyError(key)

        return key


class HVStoragePoolAccess(HVEntityAccess):
    '''Storage pool access mixin.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfStoragePools', 'numOfDefinedStoragePools'}

    @property
    def _list_func(self: Self) -> str:
        return 'listStoragePools'

    @property
    def _entity_class(self: Self) -> type:
        return StoragePool


class StoragePools(HVEntityIterator, HVStoragePoolAccess):
    '''Iterator access to domains in a Hypervisor.'''


class StoragePoolsByName(HVNameMap, HVStoragePoolAccess):
    '''A simple mapping of domain names to StoragePool instances.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storagePoolLookupByName'


class StoragePoolsByUUID(HVUUIDMap, HVStoragePoolAccess):
    '''A simple mapping of domain UUIDs to StoragePool instances.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storagePoolLookupByUUIDString'


__all__ = [
    'Hypervisor',
    'Domains',
    'DomainsByName',
    'DomainsByUUID',
    'DomainsByID',
    'StoragePools',
    'StoragePoolsByName',
    'StoragePoolsByUUID',
]
