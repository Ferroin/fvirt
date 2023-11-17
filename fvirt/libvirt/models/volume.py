# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Pydantic models for storage volume templating.'''

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class VolumeInfo(BaseModel):
    '''Model representing a volume for templating.

       The `pool_type` property should match the type of storage pool
       the volume will be defined in.'''
    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    pool_type: str = Field(min_length=1)
    allocation: int | None = Field(default=None, ge=0)
    uuid: UUID | None = Field(default=None)
    format: str | None = Field(default=None)
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
        if self.pool_type not in {'dir', 'fs'}:
            if self.nocow:
                raise ValueError('"nocow" may not be True for volumes in "{ self.pool_type }" type pools.')

        return self

    @model_validator(mode='after')
    def check_format(self: Self) -> Self:
        match self.pool_type:
            case 'dir' | 'fs' | 'netfs' | 'gluster' | 'vstorage':
                valid_formats = {
                    'raw',
                    'bochs',
                    'cloop',
                    'dmg',
                    'iso',
                    'qcow',
                    'qcow2',
                    'qed',
                    'vmdk',
                    'vpc',
                }
            case 'disk':
                valid_formats = {
                    'none',
                    'linux',
                    'fat16',
                    'fat32',
                    'linux-swap',
                    'linux-lvm',
                    'linux-raid',
                    'extended',
                }
            case 'rbd':
                valid_formats = {
                    'raw',
                }
            case _:
                valid_formats = set()

        if valid_formats:
            if self.format is not None:
                if self.format not in valid_formats:
                    raise ValueError(f'Format "{ self.format }" is not supported for volumes in "{ self.pool_type }" type pools.')
            else:
                raise ValueError(f'Format must be specified for volumes in "{ self.pool_type }" type pools.')
        elif self.format is not None:
            raise ValueError(f'Format may not be specified for volumes in "{ self.pool_type }" type pools.')

        return self

    @model_validator(mode='after')
    def set_target(self: Self) -> Self:
        if self.pool_type in {'logical', 'iscsi', 'iscsi-direct', 'scsi', 'multipath', 'zfs'}:
            self.target = False

        return self
