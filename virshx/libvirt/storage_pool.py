# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt poolains.'''

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sized, Mapping
from typing import TYPE_CHECKING, Self, Any, cast

import libvirt

from .entity import ConfigurableEntity, RunnableEntity, ConfigProperty
from .exceptions import EntityNotRunning, InsufficientPrivileges, InvalidConfig, InvalidEntity, NotConnected
from .volume import Volume
from ..util.match_alias import MatchAlias

if TYPE_CHECKING:
    from .hypervisor import Hypervisor

MATCH_ALIASES = {
    'autostart': MatchAlias(property='autostart', desc='Match on whether the pool is set to autostart or not.'),
    'device': MatchAlias(property='device', desc='Match on the pool device.'),
    'directory': MatchAlias(property='dir', desc='Match on the pool directory.'),
    'format': MatchAlias(property='format', desc='Match on the pool format.'),
    'host': MatchAlias(property='host', desc='Match on the pool host.'),
    'name': MatchAlias(property='name', desc='Match on the name of the pool.'),
    'persistent': MatchAlias(property='persistent', desc='Match on whether the pool is persistent or not.'),
    'target': MatchAlias(property='target', desc='Match on the pool target.'),
    'type': MatchAlias(property='type', desc='Match on the pool type.'),
}


class StoragePool(ConfigurableEntity, RunnableEntity):
    '''A basic class encapsulating a libvirt storage pool.

       This is a wrapper around a libvirt.virStoragePool instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.

       The volumes in the pool can be iterated over using the `volumes` property.

       Volumes in the pool can be looked up by name using the `volumes_by_name` property.'''
    type: ConfigProperty[str] = ConfigProperty(
        path='/pool/@type',
        typ=str,
    )
    capacity: ConfigProperty[int] = ConfigProperty(
        path='/pool/capacity/text()[1]',
        typ=int,
    )
    available: ConfigProperty[int] = ConfigProperty(
        path='/pool/available/text()[1]',
        typ=int,
    )
    allocated: ConfigProperty[int] = ConfigProperty(
        path='/pool/allocated/text()[1]',
        typ=int,
    )
    host: ConfigProperty[str] = ConfigProperty(
        path='/pool/source/host/@name',
        typ=str,
    )
    format: ConfigProperty[str] = ConfigProperty(
        path='/pool/source/format/@name',
        typ=str,
    )
    dir: ConfigProperty[str] = ConfigProperty(
        path='/pool/source/dir/@path',
        typ=str,
    )
    device: ConfigProperty[str] = ConfigProperty(
        path='/pool/source/device/@path',
        typ=str,
    )
    target: ConfigProperty[str] = ConfigProperty(
        path='/pool/target/path/text()[1]',
        typ=str,
    )

    def __init__(self: Self, pool: libvirt.virStoragePool | StoragePool, conn: Hypervisor) -> None:
        if isinstance(pool, StoragePool):
            pool = pool._entity

        super().__init__(pool, conn)

        self.__auto_refresh = False
        self.__volumes = Volumes(self)
        self.__volumes_by_name = VolumesByName(self)

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<virshx.libvirt.Pool: name={ self.name }, auto_refresh={ self.auto_refresh }>'
        else:
            return '<virshx.libvirt.Pool: INVALID>'

    @property
    def _format_properties(self: Self) -> set[str]:
        return super()._format_properties | {
            'autostart',
            'numVolumes',
        }

    @property
    def _define_method(self: Self) -> str:
        return 'definePool'

    @property
    def _config_flags(self: Self) -> int:
        return 0

    @property
    def volumes(self: Self) -> Volumes:
        '''An iterable of the volumes in the pool.'''
        return self.__volumes

    @property
    def volumes_by_name(self: Self) -> VolumesByName:
        '''A mapping of volume names to volumes in the pool.'''
        return self.__volumes_by_name

    @property
    def numVolumes(self: Self) -> int:
        '''The number of volumes in the pool.'''
        return len(self.volumes)

    @property
    def autostart(self: Self) -> bool:
        '''Control whether the pool starts automatically or not.

           If set to True, then the pool will be started automatically
           on system startup.'''
        self._check_valid()
        return bool(self._entity.autostart())

    @autostart.setter
    def autostart(self: Self, value: Any) -> None:
        self._check_valid()

        if self._conn.read_only:
            raise InsufficientPrivileges

        value = int(bool(value))

        self._entity.setAutostart(value)

    @property
    def auto_refresh(self: Self) -> bool:
        '''Control pool auto-refresh behavior.

           Defaults to False.

           If set to True, then operations that read the list of volumes
           in the pool will automatically call the Pool.refresh()
           method when invoked. This ensures that you will always see
           the current state of the pool when making such operations,
           but can significantly impact performance.

           This functionality is part of virshx.libvirt, not libvirt
           itself, and this property thus has no impact on libvirt
           behavior.'''
        return self.__auto_refresh

    @auto_refresh.setter
    def auto_refresh(self: Self, value: Any) -> None:
        self.__auto_refresh = bool(value)

    def refresh(self: Self) -> None:
        '''Refresh the list of volumes in the pool.

           If the auto_refresh property is set to True, this will be
           invoked automatically in most cases.'''
        self._check_valid()
        self._entity.refresh()

    def defineVolume(self: Self, config: str) -> Volume:
        '''Define a volume within the storage pool.

           Raises virshx.libvirt.InvalidConfig if config is not a valid
           libvirt volume configuration.

           Returns a Volume object for the newly defined volume on
           success.'''
        self._check_valid()

        if self._conn.read_only:
            raise InsufficientPrivileges

        if not self._conn:
            raise NotConnected

        try:
            vol = self._entity.createXML(config, flags=0)
        except libvirt.libvirtError:
            raise InvalidConfig

        return Volume(vol, self._conn, self)


class VolumesByName(Mapping):
    '''A simple mapping of names to volumes.'''
    def __init__(self: Self, pool: StoragePool) -> None:
        self._pool = pool

    def __repr__(self: Self) -> str:
        return repr(dict(self))

    def __len__(self: Self) -> int:
        self.__check_access()

        return cast(int, self._pool._entity.numOfVolumes())

    def __iter__(self: Self) -> Iterator[str]:
        self.__check_access()

        return iter(cast(list[str], self._pool._entity.listVolumes()))

    def __getitem__(self: Self, key: str) -> Volume:
        self.__check_access()

        try:
            vol = self._pool._entity.storageVolLookupByName(key)
        except libvirt.libvirtError:
            raise KeyError(key)

        return Volume(vol, self._pool._conn, self._pool)

    def __check_access(self: Self) -> None:
        if not self._pool.valid:
            raise InvalidEntity(self._pool)

        if not self._pool.running:
            raise EntityNotRunning(self._pool)

        if self._pool.auto_refresh:
            self._pool.refresh()


class Volumes(Iterable, Sized):
    '''Iterator access to volumes in a Pool.'''
    def __init__(self: Self, pool: StoragePool) -> None:
        self._pool = pool

    def __repr__(self: Self) -> str:
        if self._pool.valid:
            return f'<virshx.libvirt.Volumes: pool={ self._pool.name }>'
        else:
            return '<virshx.libvirt.Volumes: pool=INVALID>'

    def __len__(self: Self) -> int:
        self.__check_access()

        return cast(int, self._pool._entity.numOfVolumes())

    def __iter__(self: Self) -> Iterator[Volume]:
        self.__check_access()

        return iter([Volume(x, self._pool._conn, self._pool) for x in self._pool._entity.listAllVolumes()])

    def __check_access(self: Self) -> None:
        if not self._pool.valid:
            raise InvalidEntity(self._pool)

        if not self._pool.running:
            raise EntityNotRunning(self._pool)

        if self._pool.auto_refresh:
            self._pool.refresh()


__all__ = [
    'StoragePool',
    'Volumes',
    'VolumesByName',
]
