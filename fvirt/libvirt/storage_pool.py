# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt poolains.'''

from __future__ import annotations

from enum import CONTINUOUS, UNIQUE, Enum, verify
from typing import TYPE_CHECKING, Any, Final, Self, cast, overload

import libvirt

from .descriptors import ConfigProperty
from .entity import LifecycleResult, RunnableEntity
from .entity_access import BaseEntityAccess, EntityAccess, NameMap, UUIDMap
from .exceptions import EntityRunning, FeatureNotSupported, InsufficientPrivileges, InvalidConfig, NotConnected
from .volume import Volume, VolumeAccess
from ..util.match import MatchAlias

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .hypervisor import Hypervisor
    from .models.storage_pool import PoolInfo

MATCH_ALIASES: Final = {
    'autostart': MatchAlias(property='autostart', desc='Match on whether the pool is set to autostart or not.'),
    'device': MatchAlias(property='device', desc='Match on the pool device.'),
    'directory': MatchAlias(property='dir', desc='Match on the pool directory.'),
    'format': MatchAlias(property='format', desc='Match on the pool format.'),
    'host': MatchAlias(property='host', desc='Match on the pool host.'),
    'name': MatchAlias(property='name', desc='Match on the name of the pool.'),
    'persistent': MatchAlias(property='persistent', desc='Match on whether the pool is persistent or not.'),
    'target': MatchAlias(property='target', desc='Match on the pool target.'),
    'type': MatchAlias(property='pool_type', desc='Match on the pool type.'),
}


@verify(UNIQUE)
@verify(CONTINUOUS)
class StoragePoolState(Enum):
    '''Represents the state of a storage pool.'''
    UNKNOWN = -1
    INACTIVE = libvirt.VIR_STORAGE_POOL_INACTIVE
    BUILDING = libvirt.VIR_STORAGE_POOL_BUILDING
    RUNNING = libvirt.VIR_STORAGE_POOL_RUNNING
    DEGRADED = libvirt.VIR_STORAGE_POOL_DEGRADED
    INACCESSIBLE = libvirt.VIR_STORAGE_POOL_INACCESSIBLE

    def __str__(self: Self) -> str:
        return self.name.lower()


class StoragePool(RunnableEntity):
    '''A basic class encapsulating a libvirt storage pool.

       This is a wrapper around a libvirt.virStoragePool instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.

       The volumes in the pool can be iterated over using the `volumes` property.

       Volumes in the pool can be looked up by name using the `volumes_by_name` property.'''
    pool_type: ConfigProperty[str] = ConfigProperty(
        doc='The storage pool type.',
        path='./@type',
        type=str,
    )
    capacity: ConfigProperty[int] = ConfigProperty(
        doc='The total capacity of the storage pool.',
        path='./capacity',
        type=int,
    )
    available: ConfigProperty[int] = ConfigProperty(
        doc='The available space in the storage pool.',
        path='./available',
        type=int,
    )
    allocated: ConfigProperty[int] = ConfigProperty(
        doc='The allocated space within the storage pool.',
        path='./allocation',
        type=int,
    )
    host: ConfigProperty[str] = ConfigProperty(
        doc='The source host of the storage pool.',
        path='./source/host/@name',
        type=str,
    )
    format: ConfigProperty[str] = ConfigProperty(
        doc='The source format of the storage pool.',
        path='./source/format/@name',
        type=str,
    )
    dir: ConfigProperty[str] = ConfigProperty(
        doc='The source directory of the storage pool.',
        path='./source/dir/@path',
        type=str,
    )
    device: ConfigProperty[str] = ConfigProperty(
        doc='The source device of the storage pool.',
        path='./source/device/@path',
        type=str,
    )
    target: ConfigProperty[str] = ConfigProperty(
        doc='The target path of the storage pool.',
        path='./target/path',
        type=str,
    )

    @overload
    def __init__(self: Self, entity: StoragePool, parent: None = None, /) -> None: ...

    @overload
    def __init__(self: Self, entity: libvirt.virStoragePool, parent: Hypervisor, /) -> None: ...

    def __init__(self: Self, entity: libvirt.virStoragePool | StoragePool, parent: Hypervisor | None = None, /) -> None:
        super().__init__(entity, parent)

        self.__volumes = VolumeAccess(self)

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<fvirt.libvirt.StoragePool: name={ self.name }>'
        else:
            return '<fvirt.libvirt.StoragePool: INVALID>'

    @property
    def _wrapped_class(self: Self) -> Any:
        return libvirt.virStoragePool

    @property
    def _format_properties(self: Self) -> set[str]:
        return super()._format_properties | {
            'allocated',
            'autostart',
            'available',
            'capacity',
            'device',
            'dir',
            'format',
            'host',
            'num_volumes',
            'pool_type',
            'target',
        }

    @property
    def _define_method(self: Self) -> str:
        return 'define_storage_pool'

    @property
    def _config_flags(self: Self) -> int:
        return 0

    @property
    def _config_flags_inactive(self: Self) -> int:
        return cast(int, self._config_flags | libvirt.VIR_STORAGE_XML_INACTIVE)

    @property
    def volumes(self: Self) -> VolumeAccess:
        '''An iterable of the volumes in the pool.'''
        return self.__volumes

    @property
    def state(self: Self) -> StoragePoolState:
        '''The current state of the pool.'''
        self._check_valid()

        intstate = self._entity.info()[0]

        try:
            state = StoragePoolState(intstate)
        except ValueError:
            state = StoragePoolState.UNKNOWN

        return state

    @property
    def num_volumes(self: Self) -> int | None:
        '''The number of volumes in the pool, or None if the value cannot be determined.'''
        if self.running:
            return len(self.volumes)
        else:
            return None

    def build(self: Self) -> LifecycleResult:
        '''Build the storage pool.'''
        self._check_valid()

        try:
            self._entity.build(flags=0)
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def refresh(self: Self) -> LifecycleResult:
        '''Refresh the list of volumes in the pool.'''
        self._check_valid()

        try:
            self._entity.refresh()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def delete(self: Self, idempotent: bool = True) -> LifecycleResult:
        '''Delete the underlying storage resources for the pool.

           Only works on storage pools that are not running.

           May not work if the pool still has volumes in it.

           Idempotent operation only comes into effect if the pool is no
           longer valid. Deleting a valid pool is inherently idempotent.

           This is a non-recoverable destructive operation.'''
        if self.running:
            raise EntityRunning

        if not self.valid:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.FAILURE

        try:
            self._entity.delete()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def define_volume(self: Self, config: str) -> Volume:
        '''Define a volume within the storage pool.

           Raises fvirt.libvirt.InvalidConfig if config is not a valid
           libvirt volume configuration.

           Returns a Volume object for the newly defined volume on
           success.'''
        self._check_valid()

        if self._hv.read_only:
            raise InsufficientPrivileges

        if not self._hv.connected:
            raise NotConnected

        try:
            vol = self._entity.createXML(config, flags=0)
        except libvirt.libvirtError:
            raise InvalidConfig

        return Volume(vol, self)

    @staticmethod
    def _get_template_info() -> tuple[type[PoolInfo], str] | None:
        try:
            from .models.storage_pool import PoolInfo
        except ImportError:
            return None
        else:
            return (PoolInfo, 'pool.xml')


class StoragePools(BaseEntityAccess[StoragePool]):
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


class StoragePoolsByName(NameMap[StoragePool], StoragePools):
    '''Immutabkle mapping returning storage pools on a Hypervisor based on their names.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storagePoolLookupByName'


class StoragePoolsByUUID(UUIDMap[StoragePool], StoragePools):
    '''Immutabkle mapping returning storage pools on a Hypervisor based on their UUIDs.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storagePoolLookupByUUIDString'


class StoragePoolAccess(EntityAccess[StoragePool], StoragePools):
    '''Class used for accessing storage pools on a Hypervisor.

       StoragePoolAccess instances are iterable, returning the storage
       pools on the Hyopervisor in the order that libvirt returns them.

       StoragePoolAccess instances are also sized, with len(instance)
       returning the total number of storage pools on the Hypervisor.'''
    def __init__(self: Self, parent: Hypervisor) -> None:
        self.__by_name = StoragePoolsByName(parent)
        self.__by_uuid = StoragePoolsByUUID(parent)
        super().__init__(parent)

    def get(self: Self, key: Any) -> StoragePool | None:
        '''Look up a storage pool by a general identifier.'''
        return super().get(key)

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
