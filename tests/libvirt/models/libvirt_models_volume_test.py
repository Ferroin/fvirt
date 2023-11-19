# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.volume'''

from __future__ import annotations

import uuid

import pytest

from pydantic import ValidationError

from fvirt.libvirt.models.volume import VolumeInfo


@pytest.mark.parametrize('d', (
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'dir',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'allocation': 0,
        'pool_type': 'dir',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'dir',
        'format': 'raw',
        'nocow': True,
    },
    {
        'name': 'test',
        'capacity': 65536,
        'uuid': uuid.uuid4(),
        'pool_type': 'dir',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'uuid': str(uuid.uuid4()),
        'pool_type': 'dir',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'iscsi',
    },
))
def test_VolumeInfo_valid(d: dict) -> None:
    '''Check validation of known-good VolumeInfo dicts.'''
    VolumeInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'name': 'test',
        'capacity': 0,
        'allocation': 65536,
        'pool_type': 'dir',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'dir',
        'format': '',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'dir',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'uuid': '',
        'pool_type': 'dir',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'iscsi',
        'format': 'raw',
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'iscsi',
        'nocow': True,
    },
    {
        'name': 'test',
        'capacity': 65536,
        'pool_type': 'dir',
        'format': 'none',
    },
))
def test_VolumeInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad VolumeInfo dicts.'''
    with pytest.raises(ValidationError):
        VolumeInfo.model_validate(d)
