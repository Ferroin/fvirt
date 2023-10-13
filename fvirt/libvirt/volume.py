# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt storage volumes.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

import libvirt

from .entity import ConfigProperty, ConfigurableEntity, LifecycleResult
from .entity_access import BaseEntityAccess, EntityAccess, NameMap
from ..util.match import MatchAlias

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .storage_pool import StoragePool

MATCH_ALIASES = {
    'format': MatchAlias(property='format', desc='Match on the volume format.'),
    'key': MatchAlias(property='key', desc='Match on the volume key.'),
    'name': MatchAlias(property='name', desc='Match on the name of the volume.'),
    'path': MatchAlias(property='path', desc='Match on the volume path.'),
    'type': MatchAlias(property='type', desc='Match on the volume type.'),
}


class Volume(ConfigurableEntity):
    '''A basic wrapper for libvirt storage volumes.

       This is a wrapper around a libvirt.virStorageVol instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.

       Because updating most of the configuration picewise makes no sense
       for most storage volume types, all properties mirroring specific
       config values other than `name` are read-only. Configuration
       updates should be made by rewriting either the `config` or
       `configRaw`.'''
    allocation: ConfigProperty[int] = ConfigProperty(
        path='/volume/allocation',
        typ=int,
        units_to_bytes=True,
    )
    capacity: ConfigProperty[int] = ConfigProperty(
        path='/volume/capacity',
        typ=int,
        units_to_bytes=True,
    )
    type: ConfigProperty[str] = ConfigProperty(
        path='/volume/@type',
        typ=str,
    )
    format: ConfigProperty[str] = ConfigProperty(
        path='/volume/source/format/@type',
        typ=str,
    )

    def __init__(self: Self, vol: libvirt.virStorageVol | Volume, pool: StoragePool) -> None:
        if isinstance(vol, Volume):
            vol = vol._entity

        super().__init__(vol, pool)

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<fvirt.libvirt.Volume: pool={ cast(StoragePool, self._parent).name } name={ self.name }>'
        else:
            return '<fvirt.libvirt.Volume: INVALID>'

    @property
    def _format_properties(self: Self) -> set[str]:
        return super()._format_properties | {
            'key',
            'path',
            'type',
            'allocation',
            'capacity',
        }

    @property
    def _mark_invalid_on_undefine(self: Self) -> bool:
        return True

    @property
    def _define_target(self: Self) -> StoragePool:
        return cast(StoragePool, self._parent)

    @property
    def _define_method(self: Self) -> str:
        return 'defineVolume'

    @property
    def _config_flags(self: Self) -> int:
        return 0

    @property
    def key(self: Self) -> str:
        '''The volume key.

           This is a fixed identifier for the volume. Unlike the name,
           it is not guaranteed to be unique within a storage pool,
           but should uniquely identify the actual backing storage of
           the volume.'''
        return cast(str, self._entity.key())

    @property
    def path(self: Self) -> str:
        '''The path of the volume.

           The exact meaning of this is dependent on the storage pool backend.'''
        return cast(str, self._entity.path())

    def delete(self: Self, idempotent: bool = True) -> LifecycleResult:
        '''Remove the volume from the storage pool.

           This may or may not also delete the actual data of the volume.

           This is idempotent if successful and idempotent is True.

           After a successful operation, the Volume instance will become
           invalid and most methods and property access will raise a
           fvirt.libvirt.InvalidEntity exception.'''
        if not self.valid:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.NO_OPERATION

        try:
            self._entity.delete()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        self._valid = False

        return LifecycleResult.SUCCESS

    def undefine(self: Self, idempotent: bool = True) -> LifecycleResult:
        '''Alias for delete() to preserve compatibility with other entities.'''
        return self.delete(idempotent=idempotent)

    def wipe(self: Self) -> LifecycleResult:
        '''Wipe the data in the volume.

           This only ensures that subsequent accesses through libvirt
           will not read back the original data, not that the data is
           securely erased on physical media.'''
        self._check_valid()

        try:
            self._entity.wipe()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def resize(
            self: Self,
            /,
            capacity: int,
            *,
            delta: bool = False,
            shrink: bool = False,
            allocate: bool = False,
            idempotent: bool = True,
            ) -> LifecycleResult:
        '''Resize the volume to the specified capacity.

           `capacity` must be a non-negative integer. It may be rounded
           to a larger value if the hypervisor or storage pool has a
           specific allocation granularity that must be met.

           If `delta` is False (the default), then `capacity` specifies
           the absolute size in bytes that the volume should be. If
           `delta` is True, then `capacity` indicates the change in size
           in bytes relative to the current capacity.

           If `shrink` is False (the default), then attempting to reduce
           the capacity of the volume will raise a ValueError to protect
           against accidental data loss. If `shrink` is True and `delta`
           is True, the value of `capacity` will be subtracted from the
           total volume size.

           If `allocate` is True, then new space will be explicitly
           allocated for the volume to accomodate the resize operation.'''
        self._check_valid()

        if not isinstance(capacity, int):
            raise ValueError(f'{ capacity } is not an integer.')
        elif capacity < 0:
            raise ValueError('Capacity must be non-negative.')

        flags = 0

        if allocate:
            flags |= libvirt.VIR_STORAGE_VOL_RESIZE_ALLOCATE

        if shrink:
            flags |= libvirt.VIR_STORAGE_VOL_RESIZE_SHRINK
        elif capacity < self.capacity:
            raise ValueError(f'{ capacity } is less than current volume size and shrink is False.')

        if delta:
            flags |= libvirt.VIR_STORAGE_VOL_RESIZE_DELTA

            if capacity == 0:
                if idempotent:
                    return LifecycleResult.SUCCESS
                else:
                    return LifecycleResult.NO_OPERATION
        else:
            if capacity == self.capacity:
                if idempotent:
                    return LifecycleResult.SUCCESS
                else:
                    return LifecycleResult.NO_OPERATION

        try:
            self._entity.resize(capacity, flags)
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS


class Volumes(BaseEntityAccess):
    '''Volume access mixin for Entity access protocol.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfVolumes'}

    @property
    def _list_func(self: Self) -> str:
        return 'listAllVolumes'

    @property
    def _entity_class(self: Self) -> type:
        return Volume


class VolumesByName(NameMap, Volumes):
    '''Immutabkle mapping returning volumes on a StoragePool based on their names.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storageVolLookupByName'


class VolumeAccess(EntityAccess, Volumes):
    '''Class used for accessing volumes on a StoragePool.

       VolumeAccess instances are iterable, returning the volumes in
       the StoragePool in the order that libvirt returns them.

       VolumeAccess instances are also sized, with len(instance) returning
       the total number of volumes on the StoragePool.'''
    def __init__(self: Self, parent: StoragePool) -> None:
        self.__by_name = VolumesByName(parent)
        super().__init__(parent)

    @property
    def by_name(self: Self) -> VolumesByName:
        '''Mapping access to volumes by name.'''
        return self.__by_name


__all__ = [
    'Volume',
    'VolumeAccess',
    'MATCH_ALIASES',
]
