# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Pydantic models for storage volume templating.'''

from __future__ import annotations

import functools

from typing import Final, Self
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, model_validator

_FILE_POOL_TYPES: Final = {
    'dir',
    'fs',
    'netfs',
    'gluster',
    'vstorage',
}

_DISK_POOL_TYPES: Final = {
    'disk',
}

FORMATS: Final[dict[str, set[str]]] = {
    'raw': _FILE_POOL_TYPES | {'rbd'},
    'bochs': _FILE_POOL_TYPES,
    'cloop': _FILE_POOL_TYPES,
    'dmg': _FILE_POOL_TYPES,
    'iso': _FILE_POOL_TYPES,
    'qcow': _FILE_POOL_TYPES,
    'qcow2': _FILE_POOL_TYPES,
    'qed': _FILE_POOL_TYPES,
    'vmdk': _FILE_POOL_TYPES,
    'vpc': _FILE_POOL_TYPES,
    'none': _DISK_POOL_TYPES,
    'linux': _DISK_POOL_TYPES,
    'fat16': _DISK_POOL_TYPES,
    'fat32': _DISK_POOL_TYPES,
    'linux-swap': _DISK_POOL_TYPES,
    'linux-lvm': _DISK_POOL_TYPES,
    'linux-raid': _DISK_POOL_TYPES,
    'extended': _DISK_POOL_TYPES,
}

FORMAT_POOL_TYPES: Final = functools.reduce(lambda x, y: x | y, FORMATS.values())

NOCOW_POOL_TYPES: Final = {
    'dir',
    'fs',
}

TARGET_POOL_TYPES: Final = FORMAT_POOL_TYPES | NOCOW_POOL_TYPES


class VolumeInfo(BaseModel):
    '''Model representing a volume for templating.'''
    name: str = Field(
        min_length=1,
        description='Name of the volume.',
    )
    capacity: int = Field(
        gt=0,
        description='Capacity of the volume in bytes.',
    )
    pool_type: str = Field(
        min_length=1,
        description='Type of pool the volume will be created in. Will be handled automaticlaly by CLI commands.',
    )
    allocation: int | None = Field(
        default=None,
        ge=0,
        description='Amount of space allocated to the volume in bytes. Must be less than or equal to the volume capacity.',
    )
    uuid: UUID | None = Field(
        default=None,
        description='UUID of the volume. If not specified, libvirt will automatically assign a newly generated UUID.',
    )
    format: str | None = Field(
        default=None,
        pattern=f'^({"|".join(FORMATS.keys())})$',
        description='Format of the volume. Valid values depend on the pool type. See https://libvirt.org/storage.html for more information.',
    )
    nocow: bool = Field(
        default=False,
        description='Status of the NOCOW flag for the volume. ' +
                    f'Only supported for volumes in pools with one of the following types: {", ".join(NOCOW_POOL_TYPES)}',
    )

    @computed_field  # type: ignore[misc]
    @property
    def target(self: Self) -> bool:
        if self.pool_type in TARGET_POOL_TYPES:
            return True

        return False

    @model_validator(mode='after')
    def check_allocation(self: Self) -> Self:
        if self.allocation is not None:
            if self.allocation > self.capacity:
                raise ValueError('Allocated space must be less than or equal to volume capacity.')

        return self

    @model_validator(mode='after')
    def check_nocow(self: Self) -> Self:
        if self.pool_type not in NOCOW_POOL_TYPES:
            if self.nocow:
                raise ValueError('"nocow" may not be True for volumes in "{ self.pool_type }" type pools.')

        return self

    @model_validator(mode='after')
    def check_format(self: Self) -> Self:
        if self.pool_type in FORMAT_POOL_TYPES:
            if self.format is None:
                raise ValueError(f'Format must be specified for volumes in "{ self.pool_type }" type pools.')
            elif self.format not in FORMATS.keys():
                raise ValueError(f'Unrecognized format "{ self.format }"')
            else:
                if self.pool_type not in FORMATS[self.format]:
                    raise ValueError(f'Format "{ self.format }" is not supported for volumes in "{ self.pool_type }" type pools.')
        elif self.format is not None:
            raise ValueError(f'Format may not be specified for volumes in "{ self.pool_type }" type pools.')

        return self
