# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt storage volumes.'''

from __future__ import annotations

import io
import logging
import os

from typing import TYPE_CHECKING, Any, ClassVar, Final, Self, cast, overload

import libvirt

from .descriptors import ConfigProperty, MethodProperty
from .entity import Entity, LifecycleResult
from .entity_access import BaseEntityAccess, EntityAccess, EntityMap, NameMap
from .exceptions import InvalidOperation, SubOperationFailed
from .stream import Stream
from ..util.match import MatchAlias

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .models.volume import VolumeInfo
    from .storage_pool import StoragePool

LOGGER: Final = logging.getLogger(__name__)


class Volume(Entity):
    '''A basic wrapper for libvirt storage volumes.

       This is a wrapper around a libvirt.virStorageVol instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.

       Because updating most of the configuration picewise makes no sense
       for most storage volume types, all properties mirroring specific
       config values other than `name` are read-only. Configuration
       updates should be made by rewriting either the `config` or
       `configRaw`.'''
    MATCH_ALIASES: ClassVar = {
        'format': MatchAlias(property='format', desc='Match on the volume format.'),
        'key': MatchAlias(property='key', desc='Match on the volume key.'),
        'name': MatchAlias(property='name', desc='Match on the name of the volume.'),
        'path': MatchAlias(property='path', desc='Match on the volume path.'),
        'type': MatchAlias(property='vol_type', desc='Match on the volume type.'),
    }

    allocated: ConfigProperty[int] = ConfigProperty(
        doc='The actual space allocated to the volume.',
        path='./allocation',
        type=int,
        units_to_bytes=True,
    )
    capacity: ConfigProperty[int] = ConfigProperty(
        doc='The capacity of the volume.',
        path='./capacity',
        type=int,
        units_to_bytes=True,
    )
    vol_type: ConfigProperty[str] = ConfigProperty(
        doc='The volume type.',
        path='./@type',
        type=str,
    )
    format: ConfigProperty[str] = ConfigProperty(
        doc='The volume format.',
        path='./source/format/@type',
        type=str,
    )
    key: MethodProperty[str] = MethodProperty(
        doc='The volume key.',
        get='key',
        type=str,
    )
    path: MethodProperty[str] = MethodProperty(
        doc='The volume path.',
        get='path',
        type=str,
    )

    @overload
    def __init__(self: Self, entity: Volume, parent: None = None, /) -> None: ...

    @overload
    def __init__(self: Self, entity: libvirt.virStorageVol, parent: StoragePool, /) -> None: ...

    def __init__(self: Self, entity: libvirt.virStorageVol | Volume, parent: StoragePool | None = None, /) -> None:
        super().__init__(entity, parent)

    def __repr__(self: Self) -> str:
        if self.valid:
            assert self._parent is not None
            return f'<fvirt.libvirt.Volume: pool={ self._parent.name } name={ self.name }>'
        else:
            return '<fvirt.libvirt.Volume: INVALID>'

    @property
    def _wrapped_class(self: Self) -> Any:
        return libvirt.virStorageVol

    @property
    def _eq_properties(self: Self) -> set[str]:
        return {'name', 'key'}

    @property
    def _format_properties(self: Self) -> set[str]:
        return {
            'name',
            'allocated',
            'capacity',
            'key',
            'path',
            'vol_type',
            'format',
        }

    @property
    def _mark_invalid_on_undefine(self: Self) -> bool:
        return True

    @property
    def _define_target(self: Self) -> StoragePool:
        return self._parent  # type: ignore

    @property
    def _define_method(self: Self) -> str:
        return 'define_volume'

    @property
    def _config_flags(self: Self) -> int:
        return 0

    @property
    def config_raw(self: Self) -> str:
        '''The raw XML configuration of the entity.

           libvirt does not sanely support reconfiguring volumes,
           so unlike most other Entity types, trying to write to this
           property will raise an InvalidOperation error.

           For pre-parsed XML configuration, use the config property
           instead.'''
        return super().config_raw

    @config_raw.setter
    def config_raw(self: Self, value: Any) -> None:
        raise InvalidOperation

    def delete(self: Self, /, *, idempotent: bool = True) -> LifecycleResult:
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

        LOGGER.info(f'Deleting volume: {repr(self)}')

        self._entity.delete()
        self._valid = False

        return LifecycleResult.SUCCESS

    def undefine(self: Self, /, *, idempotent: bool = True) -> LifecycleResult:
        '''Alias for delete() to preserve compatibility with other entities.'''
        return self.delete(idempotent=idempotent)

    def download(self: Self, target: io.BufferedWriter, /, *, sparse: bool = False) -> int:
        '''Download the raw data from a storage volume.

           Takes a writable binary IO stream to copy the data to.

           If sparse is False, all data will be copied directly.

           If sparse is True, sparse regions in the volume will be
           detected and seekd over in the local stream.

           Returns the total number of bytes transferred, which may be
           less than the volume capacity if sparse is True.

           This is a potentially slow, long-running operation.

           This will only match what the guest sees if the volume format
           is 'raw', otherwise the downloaded data will be in whatever
           format the volume itself is in.'''
        assert self._hv._connection is not None

        stream = Stream(self._hv, sparse=sparse)

        LOGGER.info(f'Fetching data from volume: {repr(self)}')

        if sparse:
            self._entity.download(stream.stream, 0, self.capacity, libvirt.VIR_STORAGE_VOL_DOWNLOAD_SPARSE_STREAM)
        else:
            self._entity.download(stream.stream, 0, self.capacity, 0)

        stream.read_into_file(target)

        return stream.transferred

    def upload(self: Self, source: io.BufferedRandom, /, *, sparse: bool = False, resize: bool = False) -> int:
        '''Upload the raw data from a file to the volume.

           Takes a readable binary IO stream to read data from.

           If sparse is False, all data will be copied directly.

           If sparse is True, sparse regions in the source file will be
           detected and seekd over in the local stream.

           If resize is True, the volume will be resized to match the size of the source stream, and an exce

           Returns the total number of bytes transferred, which may be
           less than the volume capacity if sparse is True.

           This is a potentially slow, long-running operation.

           The source file should be in the same format as the volume
           itself (for example, if the volume is a QCOW2 volume, then
           the source file also needs to be a valid QCOW2 file.'''
        assert self._hv._connection is not None

        if resize:
            size = source.seek(0, os.SEEK_END)
            source.seek(0, os.SEEK_SET)

            match self.resize(size, shrink=(size < self.capacity)):
                case LifecycleResult.SUCCESS:
                    pass
                case _:
                    raise SubOperationFailed('Failed to resize volume.')

        stream = Stream(self._hv, sparse=sparse)

        if sparse:
            self._entity.upload(stream.stream, 0, self.capacity, libvirt.VIR_STORAGE_VOL_DOWNLOAD_SPARSE_STREAM)
        else:
            self._entity.upload(stream.stream, 0, self.capacity, 0)

        LOGGER.info(f'Uploading data to volume: {repr(self)}')

        stream.write_from_file(source)

        return stream.transferred

    def wipe(self: Self) -> LifecycleResult:
        '''Wipe the data in the volume.

           This only ensures that subsequent accesses through libvirt
           will not read back the original data, not that the data is
           securely erased on physical media.

           The exact mechanism used to achieve this is not strictly
           defined, so this may be a long running operation.'''
        self._check_valid()

        LOGGER.info(f'Wiping volume: {repr(self)}')

        self._entity.wipe()

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
        elif not delta and capacity < self.capacity:
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

        LOGGER.info(f'Resizing volume: {repr(self)}')

        self._entity.resize(capacity, flags)

        return LifecycleResult.SUCCESS

    @staticmethod
    def _get_template_info() -> tuple[type[VolumeInfo], str] | None:
        from .models.volume import VolumeInfo

        return (VolumeInfo, 'volume.xml')


class Volumes(BaseEntityAccess[Volume]):
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


class VolumesByName(NameMap[Volume], Volumes):
    '''Immutable mapping returning volumes on a StoragePool based on their names.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'storageVolLookupByName'


class VolumesByKey(EntityMap[Volume], Volumes):
    '''Immutable mapping returning Volumes on a StoragePool based on their key.'''
    def _get_key(self: Self, entity: Any) -> str:
        return cast(str, entity.key())

    def _coerce_key(self: Self, key: Any) -> str:
        if not isinstance(key, str):
            raise KeyError(key)

        return key

    @property
    def _lookup_func(self: Self) -> str:
        return 'storageVolLookupByKey'


class VolumeAccess(EntityAccess[Volume], Volumes):
    '''Class used for accessing volumes on a StoragePool.

       VolumeAccess instances are iterable, returning the volumes in
       the StoragePool in the order that libvirt returns them.

       VolumeAccess instances are also sized, with len(instance) returning
       the total number of volumes on the StoragePool.'''
    def __init__(self: Self, parent: StoragePool) -> None:
        self.__by_name = VolumesByName(parent)
        self.__by_key = VolumesByKey(parent)
        super().__init__(parent)

    @property
    def by_name(self: Self) -> VolumesByName:
        '''Mapping access to volumes by name.'''
        return self.__by_name

    @property
    def by_key(self: Self) -> VolumesByKey:
        '''Mapping access to volumes by key.'''
        return self.__by_key


__all__ = [
    'Volume',
    'VolumeAccess',
]
