# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Pydantic models for storage volume templating.'''

from __future__ import annotations

import functools

from typing import Final, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

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
    '''Model representing a volume for templating.

       The `pool_type` property should match the type of storage pool
       the volume will be defined in.'''
    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    pool_type: str = Field(min_length=1)
    allocation: int | None = Field(default=None, ge=0)
    uuid: UUID | None = Field(default=None)
    format: str | None = Field(default=None, pattern=f'^({"|".join(FORMATS.keys())})')
    nocow: bool = Field(default=False)
    target: bool = Field(default=True)

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

    @model_validator(mode='after')
    def set_target(self: Self) -> Self:
        if self.pool_type not in TARGET_POOL_TYPES:
            self.target = False

        return self
