# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt hypervisor connections.'''

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sized, Mapping
from typing import Self, cast
from types import TracebackType
from uuid import UUID

import libvirt

from .domain import Domain
from .exceptions import NotConnected, InvalidConfig, InsufficientPrivileges
from .storage_pool import StoragePool
from .uri import URI


def _count_domains(hv: Hypervisor) -> int:
    '''Count the number of domains in a Hypervisor instance.'''
    with hv as hv:
        assert hv._connection is not None

        return cast(int, hv._connection.numOfDomains()) + cast(int, hv._connection.numOfDefinedDomains())


def _count_storage_pools(hv: Hypervisor) -> int:
    '''Count the number of storage pools in a Hypervisor instance.'''
    with hv as hv:
        assert hv._connection is not None

        return cast(int, hv._connection.numOfStoragePools()) + cast(int, hv._connection.numOfDefinedStoragePools())


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
        if self.read_only:
            raise InsufficientPrivileges

        if self._connection is None:
            raise NotConnected

        try:
            dom = self._connection.defineXMLFlags(config, 0)
        except libvirt.LibvirtError:
            raise InvalidConfig

        return Domain(dom, self)

    def defineStoragePool(self: Self, config: str) -> StoragePool:
        '''Define a storage pool from an XML config string.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises virshx.libvirt.InvalidConfig if config is not a valid
           libvirt storage pool configuration.

           Returns a StoragePool instance for the defined storage pool on success.'''
        if self.read_only:
            raise InsufficientPrivileges

        if self._connection is None:
            raise NotConnected

        try:
            pool = self._connection.storagePoolDefineXML(config, 0)
        except libvirt.LibvirtError:
            raise InvalidConfig

        return StoragePool(pool, self)


class Domains(Iterable, Sized):
    '''Iterator access to domains in a Hypervisor.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.Domains: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        return _count_domains(self._hv)

    def __iter__(self: Self) -> Iterator[Domain]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listAllDomains():
                case None:
                    return iter([])
                case doms:
                    return iter([Domain(x, hv) for x in doms])


class DomainsByName(Mapping):
    '''A simple mapping of domain names to Domain instances.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.DomainsByName: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        return _count_domains(self._hv)

    def __iter__(self: Self) -> Iterator[str]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listAllDomains():
                case None:
                    return iter([])
                case doms:
                    return iter([x.name() for x in doms])

    def __getitem__(self: Self, key: str) -> Domain:
        if not isinstance(key, str):
            raise KeyError(key)

        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.lookupByName(key):
                case None:
                    raise KeyError(key)
                case domain:
                    return Domain(domain, hv)


class DomainsByUUID(Mapping):
    '''A simple mapping of domain UUIDs to Domain instances.

       On access, accepts either a UUID string, a big-endian bytes object
       representing the raw bytes of the UUID, or a pre-constructed
       UUID object. Strings and bytes are parsed as UUIDs using the uuid.UUID
       class from the Python standard library, with keys that evaulate
       to an equivalent uuid.UUID object being treated as identical.

       When iterating keys, only uuid.UUID objects will be returned.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.DomainsByName: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        return _count_domains(self._hv)

    def __iter__(self: Self) -> Iterator[UUID]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listAllDomains():
                case None:
                    return iter([])
                case doms:
                    return iter([UUID(x.UUIDString()) for x in doms])

    def __getitem__(self: Self, key: str | bytes | UUID) -> Domain:
        match key:
            case str():
                pass
            case bytes():
                key = str(UUID(bytes=key))
            case UUID():
                key = str(key)
            case _:
                raise KeyError(key)

        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.lookupByUUIDString(key):
                case None:
                    raise KeyError(key)
                case domain:
                    return Domain(domain, hv)


class DomainsByID(Mapping):
    '''A simple mapping of domain IDs to Domain instances.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.DomainsByID: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        with self._hv as hv:
            assert hv._connection is not None

            return cast(int, hv._connection.numOfDomains())

    def __iter__(self: Self) -> Iterator[str]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listDomainsID():
                case None:
                    return iter([])
                case doms:
                    return iter([x for x in doms])

    def __getitem__(self: Self, key: int) -> Domain:
        if not isinstance(key, int):
            raise KeyError(key)

        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.lookupByID(key):
                case None:
                    raise KeyError(key)
                case domain:
                    return Domain(domain, hv)


class StoragePools(Iterable, Sized):
    '''Iterator access to domains in a Hypervisor.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.StoragePools: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        return _count_storage_pools(self._hv)

    def __iter__(self: Self) -> Iterator[StoragePool]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listAllStoragePools():
                case None:
                    return iter([])
                case doms:
                    return iter([StoragePool(x, hv) for x in doms])


class StoragePoolsByName(Mapping):
    '''A simple mapping of domain names to StoragePool instances.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.StoragePoolsByName: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        return _count_storage_pools(self._hv)

    def __iter__(self: Self) -> Iterator[str]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listAllStoragePools():
                case None:
                    return iter([])
                case doms:
                    return iter([x.name() for x in doms])

    def __getitem__(self: Self, key: str) -> StoragePool:
        if not isinstance(key, str):
            raise KeyError(key)

        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.storagePoolLookupByName(key):
                case None:
                    raise KeyError(key)
                case domain:
                    return StoragePool(domain, hv)


class StoragePoolsByUUID(Mapping):
    '''A simple mapping of domain UUIDs to StoragePool instances.

       On access, accepts either a UUID string, a big-endian bytes object
       representing the raw bytes of the UUID, or a pre-constructed
       UUID object. Strings and bytes are parsed as UUIDs using the uuid.UUID
       class from the Python standard library, with keys that evaulate
       to an equivalent uuid.UUID object being treated as identical.

       When iterating keys, only uuid.UUID objects will be returned.'''
    def __init__(self: Self, hv: Hypervisor) -> None:
        self._hv = hv

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.StoragePoolsByName: hv={ repr(self._hv) }>'

    def __len__(self: Self) -> int:
        return _count_storage_pools(self._hv)

    def __iter__(self: Self) -> Iterator[UUID]:
        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.listAllStoragePools():
                case None:
                    return iter([])
                case pools:
                    return iter([UUID(x.UUIDString()) for x in pools])

    def __getitem__(self: Self, key: str | bytes | UUID) -> StoragePool:
        match key:
            case str():
                pass
            case bytes():
                key = str(UUID(bytes=key))
            case UUID():
                key = str(key)
            case _:
                raise KeyError(key)

        with self._hv as hv:
            assert hv._connection is not None

            match hv._connection.storagePoolLookupByUUIDString(key):
                case None:
                    raise KeyError(key)
                case domain:
                    return StoragePool(domain, hv)


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
