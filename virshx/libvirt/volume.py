# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt storage volumes.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

import libvirt

from ..common import unit_to_bytes
from .entity import ConfigurableEntity, ConfigProperty

if TYPE_CHECKING:
    from .hypervisor import Hypervisor
    from .storage_pool import StoragePool


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

    def __init__(self: Self, vol: libvirt.virStorageVol | Volume, conn: Hypervisor, pool: StoragePool) -> None:
        if isinstance(vol, Volume):
            vol = vol._entity

        super().__init__(vol, conn)

        self._pool = pool

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<virshx.libvirt.Volume: pool={ self._pool.name } name={ self.name }>'
        else:
            return '<virshx.libvirt.Volume: INVALID>'

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
    def _define_target(self: Self) -> StoragePool:
        return self._pool

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

    def delete(self: Self) -> bool:
        '''Remove the volume from the storage pool.

           This may or may not also delete the actual data of the volume.

           This is idempotent if successful.

           Returns True if the operation was successful, or False if it
           failed due to a libvirt error.

           After a successful operation, the Volume instance will become
           invalid and most methods and property access will raise a
           virshex.libvirt.InvalidEntity exception.'''
        if not self.valid:
            return True

        try:
            self._entity.delete()
        except libvirt.libvirtError:
            return False

        self._valid = False

        return True

    def wipe(self: Self) -> bool:
        '''Wipe the data in the volume.

           This only ensures that subsequent accesses through libvirt
           will not read back the original data, not that th edata is
           securely erased on physical media.

           Returns True if the operation was successful, or False if it
           failed due to a libvirt error.'''
        self._check_valid()

        try:
            self._entity.wipe()
        except libvirt.libvirtError:
            return False

        return True

    def resize(
            self: Self,
            /,
            capacity: int,
            *,
            delta: bool = False,
            shrink: bool = False,
            allocate: bool = False,
            ) -> bool:
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
           allocated for the volume to accomodate the resize operation.

           Returns True if the operation was successful, or False if it
           failed due to a libvirt error.'''
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

        try:
            self._entity.resize(capacity, flags)
        except libvirt.libvirtError:
            return False

        return True


__all__ = [
    'Volume',
]
