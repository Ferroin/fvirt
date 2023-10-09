# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt poolains.'''

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Self

import libvirt

from .entity import ConfigProperty, ConfigurableEntity, LifecycleResult, RunnableEntity
from .entity_access import BaseEntityAccess, EntityAccess, NameMap, UUIDMap
from .exceptions import InsufficientPrivileges, InvalidConfig, NotConnected
from .volume import Volume, VolumeAccess
from ..util.match import MatchAlias

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

        self.__volumes = VolumeAccess(self)

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<fvirt.libvirt.Pool: name={ self.name }>'
        else:
            return '<fvirt.libvirt.Pool: INVALID>'

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
    def volumes(self: Self) -> VolumeAccess:
        '''An iterable of the volumes in the pool.'''
        return self.__volumes

    @property
    def numVolumes(self: Self) -> int:
        '''The number of volumes in the pool.'''
        return len(self.volumes)

    def refresh(self: Self) -> LifecycleResult:
        '''Refresh the list of volumes in the pool.'''
        self._check_valid()

        try:
            self._entity.refresh()
        except libvirt.LibvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def delete(self: Self, idempotent: bool = True) -> LifecycleResult:
        '''Delete the underlying storage resources for the pool.

           This is a non-recoverable destructive operation.'''
        if not self.valid:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.FAILURE

        try:
            self._entity.delete()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        self.__valid = False

        return LifecycleResult.SUCCESS

    def defineVolume(self: Self, config: str) -> Volume:
        '''Define a volume within the storage pool.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt volume configuration.

           Returns a Volume object for the newly defined volume on
           success.'''
        self._check_valid()

        if self.__conn.read_only:
            raise InsufficientPrivileges

        if not self.__conn:
            raise NotConnected

        try:
            vol = self._entity.createXML(config, flags=0)
        except libvirt.libvirtError:
            raise InvalidConfig

        return Volume(vol, self.__conn, self)


class StoragePools(BaseEntityAccess):
    '''Storage pool access mixin.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfStoragePools', 'numOfDefinedStoragePools'}

    @property
    def _list_func(self: Self) -> str:
        return 'listAllStoragePools'

    @property
    def _entity_class(self: Self) -> type:
        return StoragePool


class StoragePoolsByName(NameMap, StoragePools):
    '''Immutabkle mapping returning storage pools on a Hypervisor based on their names.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storagePoolLookupByName'


class StoragePoolsByUUID(UUIDMap, StoragePools):
    '''Immutabkle mapping returning storage pools on a Hypervisor based on their UUIDs.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storagePoolLookupByUUIDString'


class StoragePoolAccess(EntityAccess, StoragePools):
    '''Class used for accessing storage pools on a Hypervisor.

       StoragePoolAccess instances are iterable, returning the storage
       pools on the Hyopervisor in the order that libvirt returns them.

       StoragePoolAccess instances are also sized, with len(instance)
       returning the total number of storage pools on the Hypervisor.'''
    def __init__(self: Self, parent: Hypervisor) -> None:
        self.__by_name = StoragePoolsByName(parent)
        self.__by_uuid = StoragePoolsByUUID(parent)
        super().__init__(parent)

    @property
    def by_name(self: Self) -> StoragePoolsByName:
        '''Mapping access to storage pools by name.'''
        return self.__by_name

    @property
    def by_uuid(self: Self) -> StoragePoolsByUUID:
        '''Mapping access to storage pools by UUID.'''
        return self.__by_uuid


__all__ = [
    'StoragePool',
    'StoragePoolAccess',
]
