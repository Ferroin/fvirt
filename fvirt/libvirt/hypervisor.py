# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt hypervisor connections.'''

from __future__ import annotations

import threading

from types import TracebackType
from typing import Any, Self, cast

import libvirt

from .domain import Domain, DomainAccess
from .entity import Entity
from .exceptions import InsufficientPrivileges, InvalidConfig
from .storage_pool import StoragePool, StoragePoolAccess
from .uri import URI
from ..version import VersionNumber


class Hypervisor:
    '''Basic class encapsulating a hypervisor connection.

       This is a wrapper around a libvirt.virConnect instance that
       provides a bunch of extra convenience functionality, such as a
       proper context manager interface and the ability to list _all_
       domains.

       Most methods of interacting with a Hypervisor instance also handle
       connection management automatically using reference counting for
       the connection itself.

       When converting to a boolean, Hypervisor instances are treated as
       false if they are not connected, and true if they have at least
       one active connection.

       Domains can be accessed via the `domains`, `domains_by_name`,
       `domains_by_id`, or `domains_by_uuid` properties.

       Storage pools can be accessed via the `pools`, `pools_by_name`,
       or `pools_by_uuid` properties.

       Internal state is protected from concurrent access using a
       threading.RLock instance. This means that Hypervisor instances are
       just as thread-safe as libvirt itself, but they are notably _not_
       asyncio safe.

       The underlying libvirt APIs are all concurrent-access safe
       irrespective of the concurrency model in use.'''
    def __init__(self: Self, hvuri: URI, read_only: bool = False) -> None:
        self._uri = hvuri

        self._connection: libvirt.virConnect | None = None
        self.__read_only = bool(read_only)
        self.__conn_count = 0
        self.__lock = threading.RLock()

        self.__domains = DomainAccess(self)

        self.__pools = StoragePoolAccess(self)

    def __repr__(self: Self) -> str:
        return f'<fvirt.libvirt.Hypervisor: uri={ str(self.uri) }, ro={ self.read_only }, conns={ self.__conn_count }>'

    def __bool__(self: Self) -> bool:
        with self.__lock:
            return self.__conn_count > 0

    def __del__(self: Self) -> None:
        with self.__lock:
            if self.__conn_count > 0:
                self.__conn_count = 0

            if self._connection is not None:
                if self._connection.isAlive():
                    self._connection.unregisterCloseCallback()
                    self._connection.close()

                self._connection = None

    def __enter__(self: Self) -> Self:
        return self.open()

    def __exit__(self: Self, _exc_type: type | None, _exc_value: BaseException | None, _traceback: TracebackType | None) -> None:
        self.close()

    def __define_entity(self: Self, entity_class: type[Entity], method: str, config: str, flags: int = 0) -> Entity:
        if self.read_only:
            raise InsufficientPrivileges

        with self:
            try:
                entity = getattr(self._connection, method)(config, flags)
            except libvirt.libvirtError:
                raise InvalidConfig

            return entity_class(entity, self)

    @property
    def read_only(self: Self) -> bool:
        return self.__read_only

    @property
    def uri(self: Self) -> URI:
        '''The canonicalized URI for this Hypervisor connection.'''
        with self:
            assert self._connection is not None
            return URI.from_string(self._connection.getURI())

    @property
    def libVersion(self: Self) -> VersionNumber:
        '''The version information of the remote libvirt instance.'''
        with self:
            assert self._connection is not None
            return VersionNumber.from_libvirt_version(self._connection.getLibVersion())

    @property
    def version(self: Self) -> VersionNumber | None:
        '''The version information of the remote hypervisor.

           Some hypervisor drivers do not report a version (such as the
           test driver), in which case this property will show a value
           of None.'''
        with self:
            assert self._connection is not None

            version = self._connection.getVersion()

            match version:
                case '':
                    return None
                case _:
                    return VersionNumber.from_libvirt_version(version)

    @property
    def connected(self: Self) -> bool:
        '''Whether or not the Hypervisor is connected.'''
        with self.__lock:
            return self._connection is not None and self._connection.isAlive()

    @property
    def domains(self: Self) -> DomainAccess:
        '''Entity access to all domains defined by the Hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__domains

    @property
    def pools(self: Self) -> StoragePoolAccess:
        '''Entity access to all pools defined by the Hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__pools

    def open(self: Self) -> Self:
        '''Open the connection represented by this Hypervisor instance.

           Hypervisor instances use reference counting to ensure that
           at most one connection is opened for any given Hypervisor
           instance. If there is already a connection open, a new one
           will not be opened.

           If the connection is lost, we will automatically try to
           reconnect.

           In most cases, it is preferred to use either the context
           manager interface, or property access, both of which will
           handle connections correctly for you.'''
        def cb(*args: Any, **kwargs: Any) -> None:
            with self.__lock:
                try:
                    if self.read_only:
                        self._connection = libvirt.openReadOnly(str(self._uri))
                    else:
                        self._connection = libvirt.open(str(self._uri))
                except libvirt.libvirtError as e:
                    raise e

                self._connection.registerCloseCallback(cb, None)

        with self.__lock:
            if self._connection is None or not self._connection.isAlive():
                try:
                    if self.read_only:
                        self._connection = libvirt.openReadOnly(str(self._uri))
                    else:
                        self._connection = libvirt.open(str(self._uri))
                except libvirt.libvirtError as e:
                    raise e

                self._connection.registerCloseCallback(cb, None)
                self.__conn_count += 1
            else:
                if self.__conn_count == 0:
                    raise RuntimeError
                else:
                    self.__conn_count += 1

        return self

    def close(self: Self) -> None:
        '''Reduce the connection count for this Hypervisor.

           If this reduces the connection count to 0, then any open
           connection is closed.

           Any open connections will also be closed when the Hypervisor
           instance is garbage-collected, so forgetting to close your
           connections is generally still safe.

           If you are using the context manager interface or the entity
           access protocols, you should not need to call this function
           manually.'''
        with self.__lock:
            if self._connection is not None and self.__conn_count < 2:
                if self._connection.isAlive():
                    self._connection.unregisterCloseCallback()
                    self._connection.close()

                self._connection = None

            self.__conn_count -= 1

            if self.__conn_count < 0:
                self.__conn_count = 0

    def defineDomain(self: Self, config: str) -> Domain:
        '''Define a domain from an XML config string.

           Raises fvirt.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt domain configuration.

           Returns a Domain instance for the defined domain on success.'''
        return cast(Domain, self.__define_entity(Domain, 'defineXMLFlags', config, 0))

    def createDomain(self: Self, config: str, paused: bool = False, reset_nvram: bool = False, auto_destroy: bool = False) -> Domain:
        '''Define and start a domain from an XML config string.

           If `paused` is True, the domain will be started in the paused state.

           If `reset_nvram` is True, any existing NVRAM file will be
           reset to a pristine state prior to starting the domain.

           If `auto_destroy` is True, the created domain will be
           automatically destroyed (forcibly stopped) when there are no
           longer any references to it or when the Hypervisor connection
           is closed.

           Raises fvirt.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt domain configuration.

           Returns a Domain instance for the defined domain on success.'''
        flags = 0

        if paused:
            flags |= libvirt.VIR_DOMAIN_START_PAUSED

        if reset_nvram:
            flags |= libvirt.VIR_DOMAIN_START_RESET_NVRAM

        if auto_destroy:
            flags |= libvirt.VIR_DOMAIN_START_AUTO_DESTROY

        return cast(Domain, self.__define_entity(Domain, 'createXML', config, flags))

    def defineStoragePool(self: Self, config: str) -> StoragePool:
        '''Define a storage pool from an XML config string.

           Raises fvirt.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt storage pool configuration.

           Returns a StoragePool instance for the defined storage pool on success.'''
        return cast(StoragePool, self.__define_entity(StoragePool, 'storagePoolDefineXML', config, 0))


__all__ = [
    'Hypervisor',
]
