# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt hypervisor connections.'''

from __future__ import annotations

import logging
import threading

from types import TracebackType
from typing import TYPE_CHECKING, Any, Final, Self, cast

import libvirt

from .exceptions import InsufficientPrivileges, call_libvirt, libvirtCallWrapper
from .uri import URI
from ..version import VersionNumber

if TYPE_CHECKING:
    from .domain import Domain, DomainAccess
    from .entity import Entity
    from .storage_pool import StoragePool, StoragePoolAccess

LOGGER: Final = logging.getLogger(__name__)


class HostInfo:
    '''Class representing basic information about a Hypervisor host.'''
    __slots__ = (
        '__arch',
        '__mem',
        '__cpus',
        '__cpufreq',
        '__nodes',
        '__sockets',
        '__cores',
        '__threads',
    )

    def __init__(
        self: Self,
        /,
        arch: str,
        mem: int,
        cpus: int,
        cpufreq: int,
        nodes: int,
        sockets: int,
        cores: int,
        threads: int,
    ) -> None:
        self.__arch = arch
        self.__mem = 1024 * 1024 * mem
        self.__cpus = cpus
        self.__cpufreq = cpufreq
        self.__nodes = nodes
        self.__sockets = sockets
        self.__cores = cores
        self.__threads = threads

    @property
    def architecture(self: Self) -> str:
        '''The CPU architecture of the host.

           This will usually match what would be returned by `uname -m`
           on a Linux system running on the host.'''
        return self.__arch

    @property
    def memory(self: Self) -> int:
        '''The total memory on the host, in bytes.

           This is an approximation as the underlying API returns the
           value in mibibytes instead of bytes.'''
        return self.__mem

    @property
    def cpus(self: Self) -> int:
        '''The total number of active logical CPU cores in the system.'''
        return self.__cpus

    @property
    def cpu_frequency(self: Self) -> int:
        '''The expected CPU frequency of the host CPU in megahertz.

           A value of 0 indicates that this information could not be obtained.

           Note that the actual CPU frequency may differ greatly from this value.'''
        return self.__cpufreq

    @property
    def nodes(self: Self) -> int:
        '''The number of NUMA nodes in the host.

           A value of 1 may indicate that the system is not a NUMA system,
           or it may indicate that the system has an unusual NUMA topology
           that libvirt cannot figure out specific information about.'''
        return self.__nodes

    @property
    def sockets(self: Self) -> int:
        '''The number of CPU sockets per NUMA node in the host.

           A value of 1 may indicate that the system has one socket per
           node, or it may indicate that the system has an unusual NUMA
           topology that libvirt cannot figure out specific information
           about.'''
        return self.__sockets

    @property
    def cores(self: Self) -> int:
        '''The number of CPU cores per socket in the host.

           If libvirt cannot figure out the specifcs of the underlying
           NUMA toplogy, this property will instead indicate the total
           number of logical processors present in the host.

           If you just care about the number of usable logical CPUs in
           the system, you should use the cpus property instead.'''
        return self.__cores

    @property
    def threads(self: Self) -> int:
        '''The number of threads per CPU core in the host.

           A value of 1 may indicate that the system has one thread per
           core, or it may indicate that the system has an unusual NUMA
           topology that libvirt cannot figure out specific information
           about.'''
        return self.__threads


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

       Hypervisor instances are considered to be equal if their read_only
       attributes are the same and they were instantiated with equal URIs.

       Domains can be accessed via the `domains` property using the
       EntityAccess protocol.

       Storage pools can be accessed via the `storage_pools` property
       using the EntityAccess protocol.

       Internal state is protected from concurrent access using a
       threading.RLock instance. This means that Hypervisor instances are
       just as thread-safe as libvirt itself, but they are notably _not_
       asyncio safe.

       The underlying libvirt APIs are all concurrent-access safe
       irrespective of the concurrency model in use.'''
    def __init__(self: Self, hvuri: URI, read_only: bool = False) -> None:
        from .domain import DomainAccess
        from .storage_pool import StoragePoolAccess

        self._uri = hvuri

        self._connection: libvirtCallWrapper[libvirt.virConnect] | None = None

        self.__read_only = bool(read_only)
        self.__conn_count = 0
        self.__lock = threading.RLock()

        self.__domains = DomainAccess(self)

        self.__storage_pools = StoragePoolAccess(self)

        LOGGER.debug(f'Initialized new hypervisor instance: {repr(self)}')

    def __del__(self: Self) -> None:
        with self.__lock:
            LOGGER.debug(f'Tearing down hypervisor instance: {repr(self)}')

            if self.__conn_count > 0:
                self.__conn_count = 0

            if self._connection is not None:
                if self._connection.isAlive():
                    self._connection.unregisterCloseCallback()
                    self._connection.close()

                self._connection = None

    def __repr__(self: Self) -> str:
        return f'<fvirt.libvirt.Hypervisor: uri={ str(self._uri) }, ro={ self.read_only }, conns={ self.__conn_count }>'

    def __bool__(self: Self) -> bool:
        with self.__lock:
            return self.__conn_count > 0

    def __eq__(self: Self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False

        # This intentionally checks the local URI instead of the remote one.
        # This avoids connecting to a remote system potentially twice
        # just to check object equality, but introduces an edge case where
        # two functionally equivalent Hypervisor instances do not compare
        # equal if their local URIs differ.
        return self._uri == other._uri and self.read_only == other.read_only

    def __enter__(self: Self) -> Self:
        return self.open()

    def __exit__(self: Self, _exc_type: type | None, _exc_value: BaseException | None, _traceback: TracebackType | None) -> None:
        self.close()

    def __define_entity(self: Self, entity_class: type[Entity], method: str, config: str, flags: int = 0) -> Entity:
        if self.read_only:
            raise InsufficientPrivileges

        with self:
            entity = getattr(self._connection, method)(config, flags)

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
    def lib_version(self: Self) -> VersionNumber:
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
    def storage_pools(self: Self) -> StoragePoolAccess:
        '''Entity access to all pools defined by the Hypervisor.

           Automatically manages a connection when accessed.'''
        return self.__storage_pools

    @property
    def host_info(self: Self) -> HostInfo:
        '''Assorted information about the hypervisor host.'''
        with self:
            assert self._connection is not None

            return HostInfo(*self._connection.getInfo())

    @property
    def hostname(self: Self) -> str:
        '''The host name of the hypervisor host.'''
        with self:
            assert self._connection is not None

            return cast(str, self._connection.getHostname())

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
        # TODO: Figure out some way to test reconnect handling
        def cb(*args: Any, **kwargs: Any) -> None:
            with self.__lock:
                if self.read_only:
                    self._connection = libvirtCallWrapper(call_libvirt(lambda: libvirt.openReadOnly(str(self._uri))))
                else:
                    self._connection = libvirtCallWrapper(call_libvirt(lambda: libvirt.open(str(self._uri))))

                self._connection.registerCloseCallback(cb, None)

        with self.__lock:
            if self._connection is None or not self._connection.isAlive():
                LOGGER.debug(f'Opening new connection for hypervisor instance: {repr(self)}')

                if self.read_only:
                    self._connection = libvirtCallWrapper(call_libvirt(lambda: libvirt.openReadOnly(str(self._uri))))
                else:
                    self._connection = libvirtCallWrapper(call_libvirt(lambda: libvirt.open(str(self._uri))))

                self._connection.registerCloseCallback(cb, None)
                self.__conn_count += 1
            else:
                LOGGER.debug(f'Registering new connection user for hypervisor instance: {repr(self)}')

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
                LOGGER.debug(f'Closing connection for hypervisor: {repr(self)}')

                if self._connection.isAlive():
                    self._connection.unregisterCloseCallback()
                    self._connection.close()

                self._connection = None
            else:
                LOGGER.debug(f'Unregistering user for hypervisor connection: {repr(self)}')

            self.__conn_count -= 1

            if self.__conn_count < 0:
                self.__conn_count = 0

    def define_domain(self: Self, config: str) -> Domain:
        '''Define a domain from an XML config string.

           Raises fvirt.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt domain configuration.

           Returns a Domain instance for the defined domain on success.'''
        from .domain import Domain

        LOGGER.info(f'Creating new persistent domain in hypervisor: {repr(self)}')

        return cast(Domain, self.__define_entity(Domain, 'defineXMLFlags', config, 0))

    def create_domain(self: Self, config: str, paused: bool = False, reset_nvram: bool = False, auto_destroy: bool = False) -> Domain:
        '''Create a domain from an XML config string.

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
        from .domain import Domain

        flags = 0

        if paused:
            flags |= libvirt.VIR_DOMAIN_START_PAUSED

        if reset_nvram:
            flags |= libvirt.VIR_DOMAIN_START_RESET_NVRAM

        if auto_destroy:
            flags |= libvirt.VIR_DOMAIN_START_AUTO_DESTROY

        LOGGER.info(f'Creating new transient domain in hypervisor: {repr(self)}')

        return cast(Domain, self.__define_entity(Domain, 'createXML', config, flags))

    def define_storage_pool(self: Self, config: str) -> StoragePool:
        '''Define a storage pool from an XML config string.

           Raises fvirt.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt storage pool configuration.

           Returns a StoragePool instance for the defined storage pool
           on success.'''
        from .storage_pool import StoragePool

        LOGGER.info(f'Creating new persistent storage pool in hypervisor: {repr(self)}')

        return cast(StoragePool, self.__define_entity(StoragePool, 'storagePoolDefineXML', config, 0))

    def create_storage_pool(self: Self, config: str, build: bool = True, overwrite: bool | None = None) -> StoragePool:
        '''Create a storage pool from an XML config string.

           If `build` is True, then the pool will also be built during creation.

           The `overwrite` argument controls how overwrites are handled
           when build is True, if None then no preference is epxressed. If
           True, then any existing data will be overwritten. If False,
           then creation will fail if data would be overwritten.

           Raises fvirt.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt storage pool configuration.

           Returns a StoragePool instance for the defined storage pool
           on success.'''
        from .storage_pool import StoragePool

        flags = 0

        if build:
            match overwrite:
                case True:
                    flags |= libvirt.VIR_STORAGE_POOL_CREATE_WITH_BUILD_OVERWRITE
                case False:
                    flags |= libvirt.VIR_STORAGE_POOL_CREATE_WITH_BUILD_NO_OVERWRITE
                case None:
                    flags |= libvirt.VIR_STORAGE_POOL_CREATE_WITH_BUILD
                case _:
                    raise RuntimeError

        LOGGER.info(f'Creating new transient storage pool in hypervisor: {repr(self)}')

        return cast(StoragePool, self.__define_entity(StoragePool, 'storagePoolCreateXML', config, flags))


__all__ = [
    'Hypervisor',
]
