# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.storage_pool'''

from __future__ import annotations

import uuid

import pytest

from pydantic import ValidationError

from fvirt.libvirt.models.storage_pool import PoolFeatures, PoolInfo, PoolSource, PoolTarget


@pytest.mark.parametrize('d', (
    dict(),
    {
        'cow': 'yes',
    },
    {
        'cow': 'no',
    },
    {
        'cow': None,
    },
))
def test_PoolFeatures_valid(d: dict) -> None:
    '''Check validation of known-good PoolFeatures dicts.'''
    PoolFeatures.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'cow': 'foo',
    },
))
def test_PoolFeatures_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolFeatures dicts.'''
    with pytest.raises(ValidationError):
        PoolFeatures.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'format': 'auto',
    },
    {
        'dir': 'test',
    },
    {
        'initiator': 'test',
    },
    {
        'adapter': 'test',
    },
    {
        'name': 'test',
    },
    {
        'hosts': [
            'test',
        ],
    },
    {
        'devices': [
            'test',
        ],
    },
))
def test_PoolSource_valid(d: dict) -> None:
    '''Check validation of known-good PoolSource dicts.'''
    PoolSource.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'format': '',
    },
    {
        'dir': '',
    },
    {
        'initiator': '',
    },
    {
        'adapter': '',
    },
    {
        'name': '',
    },
    {
        'hosts': [],
    },
    {
        'devices': [],
    },
))
def test_PoolSource_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolSource dicts.'''
    with pytest.raises(ValidationError):
        PoolSource.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'path': '/nonexistent',
    },
))
def test_PoolTarget_valid(d: dict) -> None:
    '''Check validation of known-good PoolTarget dicts.'''
    PoolTarget.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'path': None,
    },
    {
        'path': '',
    },
))
def test_PoolTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolTarget dicts.'''
    with pytest.raises(ValidationError):
        PoolTarget.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'dir',
        'name': 'test',
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'dir',
        'name': 'test',
        'uuid': uuid.uuid4(),
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'dir',
        'name': 'test',
        'uuid': str(uuid.uuid4()),
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'dir',
        'name': 'test',
        'features': {
            'cow': 'no',
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'fs',
        'name': 'test',
        'source': {
            'format': 'auto',
            'devices': [
                '/dev/sda1',
            ],
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'netfs',
        'name': 'test',
        'source': {
            'format': 'nfs',
            'hosts': [
                'nfs.example.com',
            ],
            'dir': '/pool',
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'multipath',
        'name': 'test',
    },
    {
        'type': 'zfs',
        'name': 'test',
        'source': {
            'name': 'test',
        },
    },
))
def test_PoolInfo_valid(d: dict) -> None:
    '''Check validation of known-good PoolInfo dicts.'''
    PoolInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': 'bogus',
        'name': 'test',
    },
    {
        'type': 'dir',
        'name': 'test',
    },
    {
        'type': 'dir',
        'name': 'test',
        'uuid': '',
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'dir',
        'name': 'test',
        'features': {
            'cow': '',
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'fs',
        'name': 'test',
        'source': {
            'format': '',
            'devices': [
                '/dev/sda1',
            ],
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'fs',
        'name': 'test',
        'source': {
            'format': 'none',
            'devices': [
                '/dev/sda1',
            ],
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'fs',
        'name': 'test',
        'source': {
            'format': 'auto',
            'devices': [
                '/dev/sda1',
                '/dev/sda2',
            ],
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'netfs',
        'name': 'test',
        'source': {
            'format': 'nfs',
            'hosts': [
                'nfs.example.com',
            ],
        },
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'iscsi-direct',
        'name': 'test',
        'source': {
            'hosts': [
                'iscsi1.example.com',
                'iscsi2.example.com',
            ],
            'devices': [
                'iqn.2013-06.com.example:iscsi-pool',
            ],
            'initiator': 'iqn.2013-06.com.example:iscsi-initiator',
        },
    },
    {
        'type': 'iscsi-direct',
        'name': 'test',
        'source': {
            'hosts': [
                'iscsi.example.com',
            ],
            'devices': [
                'iqn.2013-06.com.example:iscsi-pool',
            ],
        },
    },
    {
        'type': 'scsi',
        'name': 'test',
        'source': {
            'devices': [
                '/dev/sda1',
            ],
        }
    },
    {
        'type': 'multipath',
        'name': 'test',
        'features': {
            'cow': 'no',
        },
    },
    {
        'type': 'multipath',
        'name': 'test',
        'target': {
            'path': '/nonexistent',
        },
    },
    {
        'type': 'multipath',
        'name': 'test',
        'source': {
            'name': 'test',
        },
    },
    {
        'type': 'zfs',
        'name': 'test',
        'source': {
            'devices': [
                '/dev/sda1',
            ],
        },
    },
))
def test_PoolInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolInfo dicts.'''
    with pytest.raises(ValidationError):
        PoolInfo.model_validate(d)
