# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.domain'''

from __future__ import annotations

import itertools

import pytest

from psutil import cpu_count
from pydantic import ValidationError

from fvirt.libvirt.models.domain import (CPUInfo, CPUModelInfo, CPUTopology, DataRate, DriveAddress, MemtuneInfo, OSContainerIDMapEntry,
                                         OSContainerIDMapInfo, OSFWLoaderInfo, OSFWNVRAMInfo, OSInfo, PCIAddress)


@pytest.mark.parametrize('d', (
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
    },
    {
        'bus': '0xf8',
        'slot': '0x21',
        'function': '0xc',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
        'domain': '0x0000',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
        'multifunction': 'on',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
        'domain': '0x0000',
        'multifunction': 'off',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
        'domain': None,
        'multifunction': None,
    },
))
def test_PCIAddress_valid(d: dict) -> None:
    '''Check validation of known-good PCI addresses.'''
    PCIAddress.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'bus': '',
        'slot': '0x00',
        'function': '0x0',
    },
    {
        'bus': '0x00',
        'slot': '',
        'function': '0x0',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '',
    },
    {
        'slot': '0x00',
        'function': '0x0',
    },
    {
        'bus': '0x00',
        'function': '0x0',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': None,
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
        'domain': '',
    },
    {
        'bus': '0x00',
        'slot': '0x00',
        'function': '0x0',
        'multifunction': 'foo',
    },
))
def test_PCIAddress_invalid(d: dict) -> None:
    '''Check validation of known-bad PCI addresses.'''
    with pytest.raises(ValidationError):
        PCIAddress.model_validate(d)


drive_addr_keys = [
    'target',
    'bus',
    'unit',
    'controller',
]


@pytest.mark.parametrize('d', tuple(
    dict(zip(keys, [1] * len(drive_addr_keys)))
    for keyset in [itertools.combinations(drive_addr_keys, i) for i in range(1, len(drive_addr_keys) + 1)]
    for keys in keyset
))
def test_DriveAddress_valid(d: dict) -> None:
    '''Check validation of known-good drive addresses.'''
    DriveAddress.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'bus': None,
    },
    {
        'target': None,
    },
    {
        'unit': None,
    },
    {
        'bus': -1,
    },
    {
        'target': -1,
    },
    {
        'unit': -1,
    },
    {
        'controller': -1,
    },
))
def test_DriveAddress_invalid(d: dict) -> None:
    '''Check validation of known-bad drive addresses.'''
    with pytest.raises(ValidationError):
        DriveAddress.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'bytes': 1,
    },
    {
        'bytes': 1e10,
    },
    {
        'bytes': 1,
        'period': None,
    },
    {
        'bytes': 1,
        'period': 1,
    },
    {
        'bytes': 1e10,
        'period': 1e10,
    },
))
def test_DataRate_valid(d: dict) -> None:
    '''Check validation of known-good DataRate dicts.'''
    DataRate.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'bytes': 0,
    },
    {
        'bytes': -1,
    },
    {
        'bytes': '',
    },
    {
        'bytes': 1,
        'period': 0,
    },
    {
        'bytes': 1,
        'period': -1,
    },
    {
        'bytes': 1,
        'period': '',
    },
    {
        'period': 1,
    },
))
def test_DataRate_invalid(d: dict) -> None:
    '''Check validation of known-bad DataRate dicts.'''
    with pytest.raises(ValidationError):
        DataRate.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'hard': 1024,
    },
    {
        'soft': 1024,
    },
    {
        'swap': 1024,
    },
    {
        'min': 1024,
    },
    {
        'hard': 1024,
        'soft': 1024,
        'swap': 1024,
        'min': 1024,
    },
))
def test_MemtuneInfo_valid(d: dict) -> None:
    '''Check validation of known-good MemtuneInfo dicts.'''
    MemtuneInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'hard': '',
    },
    {
        'soft': 0,
    },
    {
        'swap': 0.5,
    },
))
def test_MemtuneInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad MemtuneInfo dicts.'''
    with pytest.raises(ValidationError):
        MemtuneInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'name': 'test',
    },
    {
        'name': 'test',
        'fallback': None,
    },
    {
        'name': 'test',
        'fallback': 'test',
    },
))
def test_CPUModelInfo_valid(d: dict) -> None:
    '''Check validation of known-good CPUModelInfo dicts.'''
    CPUModelInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'name': '',
    },
    {
        'name': 'test',
        'fallback': '',
    },
))
def test_CPUModelInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad CPUModelInfo dicts.'''
    with pytest.raises(ValidationError):
        CPUModelInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'sockets': 2,
        'dies': 2,
        'cores': 2,
        'threads': 2,
    },
    {
        'infer': 'threads',
    },
    {
        'coalesce': 'sockets',
    },
))
def test_CPUTopology_valid(d: dict) -> None:
    '''Check validation of known-good CPUTopology dicts.'''
    CPUTopology.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'sockets': 0,
    },
    {
        'dies': 0,
    },
    {
        'cores': 0,
    },
    {
        'threads': 0,
    },
    {
        'infer': '',
    },
    {
        'coalesce': '',
    },
))
def test_CPUTopology_invalid(d: dict) -> None:
    '''Check validation of known-bad CPUTopology dicts.'''
    with pytest.raises(ValidationError):
        CPUTopology.model_validate(d)


@pytest.mark.parametrize('d, e', (
    (dict(), 1),
    ({
        'cores': 4,
    }, 4),
    ({
        'sockets': 2,
        'cores': 2,
        'threads': 2,
    }, 8),
    ({
        'dies': 2,
    }, 2),
))
def test_CPUTopology_total_cpus(d: dict, e: int) -> None:
    '''Check behavior of the total_cpus property for CPUTopology instances.'''
    model = CPUTopology.model_validate(d)

    assert model.total_cpus == e


@pytest.mark.parametrize('d, v, c', (
    (dict(), 1, None),
    (dict(), 2, None),
    ({
        'coalesce': 'cores',
    }, 8, 'cores'),
    ({
        'coalesce': 'sockets',
        'sockets': 8,
        'dies': 12,
        'cores': 2,
        'threads': 2,
    }, 4, 'sockets'),
    ({
        'sockets': 8,
        'dies': 2,
        'cores': 2,
        'threads': 2,
    }, 8, None),
))
def test_CPUTopology_check(d: dict, v: int, c: str | None) -> None:
    '''Check behavior of the CPUTopology.check method.'''
    model = CPUTopology.model_validate(d)

    model.check(v)

    assert model.total_cpus == v

    if c is not None:
        assert getattr(model, c) == v


def test_CPUTopology_check_bad_vcpus() -> None:
    '''Check that CPUTopology.check raises an error if passed a value less than 1.'''
    model = CPUTopology()

    with pytest.raises(ValueError):
        model.check(0)


def test_CPUTopology_infer_threads() -> None:
    '''Check that inferring threads for CPUTopology works.'''
    lcpus = cpu_count(logical=True)
    pcpus = cpu_count(logical=False)

    if lcpus is None or pcpus is None:
        pytest.skip('Unable to infer CPU topology on this system, skipping test.')

    model = CPUTopology(
        infer='threads',
    )

    assert model.threads == lcpus // pcpus


@pytest.mark.parametrize('d', (
    dict(),
    {
        'mode': None,
        'model': {
            'name': 'test',
        },
    },
    {
        'mode': None,
        'model': {
            'name': 'test',
        },
        'topology': {
            'sockets': 2,
            'dies': 2,
            'cores': 2,
            'threads': 2,
        },
    },
))
def test_CPUInfo_valid(d: dict) -> None:
    '''Check validation of known-good CPUInfo dicts.'''
    CPUInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'mode': '',
    },
))
def test_CPUInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad CPUInfo dicts.'''
    with pytest.raises(ValidationError):
        CPUInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'path': '/nonexistent',
    },
    {
        'path': '/nonexistent',
        'secure': 'yes',
    },
    {
        'secure': 'no',
        'stateless': 'yes',
    },
    {
        'path': '/nonexistent',
        'type': 'pflash',
        'readonly': 'yes',
    },
))
def test_OSFWLoaderInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSFWLoaderInfo dicts.'''
    OSFWLoaderInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'path': '',
    },
    {
        'readonly': 'foo',
    },
    {
        'secure': 'foo',
    },
    {
        'stateless': 'foo',
    },
    {
        'type': '',
    },
))
def test_OSFWLoaderInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSFWLoaderInfo dicts.'''
    with pytest.raises(ValidationError):
        OSFWLoaderInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'path': '/nonexistent',
        'template': '/nonexistent2',
    },
))
def test_OSFWNVRAMInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSFWNVRAMInfo dicts.'''
    OSFWNVRAMInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'path': '/nonexistent',
        'template': '',
    },
    {
        'path': '',
        'template': '/nonexistent',
    },
    {
        'path': '',
        'template': '',
    },
    {
        'path': '/nonexistent',
        'template': None,
    },
))
def test_OSFWNVRAMInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSFWNVRAMInfo dicts.'''
    with pytest.raises(ValidationError):
        OSFWNVRAMInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'target': 0,
        'count': 1,
    },
    {
        'target': 65536,
        'count': 65536,
    },
))
def test_OSContainerIDMapEntry_valid(d: dict) -> None:
    '''Check validation of known-good OSContainerIDMapEntry dicts.'''
    OSContainerIDMapEntry.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'target': 0,
    },
    {
        'count': 1,
    },
    {
        'target': -1,
        'count': 1,
    },
    {
        'target': 0,
        'count': 0,
    },
))
def test_OSContainerIDMapEntry_invalid(d: dict) -> None:
    '''Check validation of known-bad OSContainerIDMapEntry dicts.'''
    with pytest.raises(ValidationError):
        OSContainerIDMapEntry.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'uid': {
            'target': 0,
            'count': 1,
        },
        'gid': {
            'target': 0,
            'count': 1,
        },
    },
    {
        'uid': {
            'target': 0,
            'count': 65536,
        },
        'gid': {
            'target': 65536,
            'count': 1,
        },
    },
))
def test_OSContainerIDMapInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSContainerIDMapInfo dicts.'''
    OSContainerIDMapInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'uid': {
            'target': 0,
            'count': 1,
        },
        'gid': None,
    },
    {
        'uid': None,
        'gid': {
            'target': 0,
            'count': 1,
        },
    },
    {
        'uid': {
            'target': 0,
            'count': 1,
        },
    },
    {
        'gid': {
            'target': 0,
            'count': 1,
        },
    },
))
def test_OSContainerIDMapInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSContainerIDMapInfo dicts.'''
    with pytest.raises(ValidationError):
        OSContainerIDMapInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'variant': 'firmware',
    },
    {
        'variant': 'firmware',
        'arch': 'x86_64',
    },
    {
        'variant': 'firmware',
        'machine': 'q35',
    },
    {
        'variant': 'firmware',
        'type': 'linux',
    },
    {
        'variant': 'firmware',
        'firmware': 'efi',
        'loader': {
            'secure': 'yes',
        },
    },
    {
        'variant': 'firmware',
        'loader': {
            'path': '/nonexistent1',
            'type': 'pflash',
            'readonly': 'yes',
        },
    },
    {
        'variant': 'firmware',
        'loader': {
            'path': '/nonexistent1',
            'type': 'pflash',
            'readonly': 'yes',
        },
        'nvram': {
            'path': '/nonexistent2',
            'template': '/nonexistent3',
        },
    },
))
def test_OSInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSInfo dicts.'''
    OSInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'variant': 'firmware',
        'loader': '/nonexistent',
    },
    {
        'variant': 'firmware',
        'nvram': {
            'path': '/nonexistent1',
            'template': '/nonexistent2',
        },
    },
    {
        'variant': 'firmware',
        'bootloader': '/nonexistent',
    },
    {
        'variant': 'firmware',
        'init': '/nonexistent',
    },
))
def test_OSInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSInfo dicts.'''
    with pytest.raises(ValidationError):
        OSInfo.model_validate(d)
