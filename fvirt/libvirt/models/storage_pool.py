# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Pydantic models for storage pool templating.'''

from __future__ import annotations

from collections.abc import Sequence
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PoolFeatures(BaseModel):
    '''Model representing features for a storage pool.'''
    cow: str | None = Field(default=None, pattern='^(yes|no)$')


class PoolSource(BaseModel):
    '''Model representing the source for a storage pool.'''
    format: str | None = Field(default=None, min_length=1)
    dir: str | None = Field(default=None, min_length=1)
    devices: Sequence[str] | None = Field(default=None)
    hosts: Sequence[str] | None = Field(default=None)
    initiator: str | None = Field(default=None, min_length=1)
    adapter: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)


class PoolTarget(BaseModel):
    '''Model representing the target for a storage pool.'''
    path: str = Field(min_length=1)


class PoolInfo(BaseModel):
    '''Model representing a storage pool for templating.'''
    type: str = Field(pattern='^(dir|(net)?fs|logical|disk|iscsi(-direct)?|scsi|multipath|rbd|gluster|zfs|vstorage)$')
    name: str = Field(min_length=1)
    uuid: UUID | None = Field(default=None)
    features: PoolFeatures | None = Field(default=None)
    source: PoolSource | None = Field(default=None)
    target: PoolTarget | None = Field(default=None)

    @model_validator(mode='after')
    def check_features(self: Self) -> Self:
        if self.features is None:
            return self

        if self.features.cow is not None and self.type not in {'dir', 'fs'}:
            raise ValueError('The "cow" feature may only be specified for "dir" or "fs" type pools.')

        return self

    @model_validator(mode='after')
    def check_source(self: Self) -> Self:
        if self.type in {'dir', 'multipath'}:
            if self.source is not None:
                raise ValueError(f'Sources are not supported for "{ self.type }" type pools.')

            return self

        if self.source is None:
            raise ValueError(f'Source must be specified for "{ self.type }" type pools.')

        invalid_source_props = set(PoolSource.__annotations__.keys())

        if self.type == 'fs':
            invalid_source_props.discard('format')
            valid_formats = {
                'auto',
                'ext2',
                'ext3',
                'ext4',
                'ufs',
                'iso9660',
                'udf',
                'gfs',
                'gfs2',
                'vfat',
                'hfs+',
                'xfs',
                'ocfs2',
                'vmfs',
            }
        elif self.type == 'netfs':
            invalid_source_props.discard('format')
            valid_formats = {
                'auto',
                'nfs',
                'gluster',
                'cifs',
            }
        elif self.type == 'disk':
            invalid_source_props.discard('format')
            valid_formats = {
                'dos',
                'gpt',
                'dvh',
                'mac',
                'bsd',
                'pc98',
                'sun',
            }
        else:
            valid_formats = set()

        if valid_formats:
            if self.source.format is None:
                raise ValueError(f'Source format must be specified for "{ self.type }" type pools.')
            elif self.source.format not in valid_formats:
                raise ValueError(f'Source format "{ self.source.format }" is not valid for "{ self.type }" type pools.')

        if self.type in {'netfs', 'gluster'}:
            if self.source.dir is None:
                raise ValueError(f'Source directory must be specified for "{ self.type }" type pools.')

            invalid_source_props.discard('dir')

        if self.type == 'zfs':
            invalid_source_props.discard('devices')

        if self.type in {'fs', 'logical', 'disk', 'iscsi', 'iscsi-direct'}:
            if self.source.devices is None:
                raise ValueError(f'Source device must be specified for "{ self.type }" type pools.')

            invalid_source_props.discard('devices')

            if self.type in {'fs', 'disk', 'iscsi', 'iscsi-direct'}:
                if len(self.source.devices) != 1:
                    raise ValueError(f'Only one source device may be specified for "{ self.type }" type pools.')

        if self.type in {'netfs', 'iscsi', 'iscsi-direct', 'rbd', 'gluster'}:
            if not self.source.hosts:
                raise ValueError(f'Source host must be specified for "{ self.type }" type pools.')

            invalid_source_props.discard('hosts')

            if self.type in {'netfs', 'iscsi', 'iscsi-direct'}:
                if len(self.source.hosts) != 1:
                    raise ValueError(f'Only one source host may be specified for "{ self.type }" type pools.')

        if self.type in {'iscsi-direct'}:
            if not self.source.initiator:
                raise ValueError(f'Source initiator must be specified for "{ self.type }" type pools.')

            invalid_source_props.discard('initiator')

        if self.type in {'scsi'}:
            if not self.source.adapter:
                raise ValueError(f'Source adapter must be specified for "{ self.type }" type pools.')

            invalid_source_props.discard('adapter')

        if self.type in {'rbd', 'gluster', 'zfs', 'vstorage'}:
            if not self.source.name:
                raise ValueError(f'Source name must be specified for "{ self.type }" type pools.')

            invalid_source_props.discard('name')

        for prop in invalid_source_props:
            if getattr(self.source, prop) is not None:
                raise ValueError(f'Source { prop } is not supported for "{ self.type }" type pools.')

        return self

    @model_validator(mode='after')
    def check_target(self: Self) -> Self:
        if self.type in {'dir', 'fs', 'netfs', 'logical', 'disk', 'iscsi', 'scsi', 'vstorage'}:
            if self.target is None:
                raise ValueError(f'Target must be specified for "{ self.type }" type pools.')
        else:
            if self.target is not None:
                raise ValueError(f'Target is not supported for "{ self.type }" type pools.')

            return self

        return self
