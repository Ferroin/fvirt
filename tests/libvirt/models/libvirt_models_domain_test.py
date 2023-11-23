# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.domain'''

from __future__ import annotations

import itertools

import pytest

from psutil import cpu_count
from pydantic import ValidationError

from fvirt.libvirt.models.domain import (CharacterDevice, CharDevLog, CharDevSource, CharDevTarget, ClockInfo, ClockTimerInfo, ControllerDevice,
                                         ControllerDriverInfo, CPUInfo, CPUModelInfo, CPUTopology, DataRate, Devices, DiskDevice, DiskTargetInfo,
                                         DiskVolumeSrcInfo, DomainInfo, DriveAddress, FeaturesAPICInfo, FeaturesCapabilities, FeaturesGICInfo,
                                         FeaturesHyperVInfo, FeaturesHyperVSpinlocks, FeaturesHyperVSTimer, FeaturesHyperVVendorID, FeaturesInfo,
                                         FeaturesIOAPICInfo, FeaturesKVMDirtyRing, FeaturesKVMInfo, FeaturesTCGInfo, FeaturesXenInfo,
                                         FeaturesXenPassthrough, Filesystem, FilesystemDriverInfo, GraphicsDevice, GraphicsListener, InputDevice,
                                         InputSource, MemtuneInfo, NetworkInterface, NetworkIPInfo, NetworkVPort, OSContainerIDMapEntry,
                                         OSContainerIDMapInfo, OSFWLoaderInfo, OSFWNVRAMInfo, OSInfo, PCIAddress, RNGBackend, RNGDevice,
                                         SimpleDevice, TPMDevice, VideoDevice, WatchdogDevice)


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
    {
        'variant': 'host',
        'bootloader': '/usr/bin/boot',
    },
    {
        'variant': 'host',
        'bootloader': '/usr/bin/boot',
        'bootloader_args': 'test',
    },
    {
        'variant': 'direct',
        'kernel': 'test',
    },
    {
        'variant': 'direct',
        'kernel': 'test',
        'initrd': 'test',
    },
    {
        'variant': 'direct',
        'kernel': 'test',
        'cmdline': 'test',
    },
    {
        'variant': 'direct',
        'kernel': 'test',
        'dtb': 'test',
    },
    {
        'variant': 'direct',
        'kernel': 'test',
        'loader': 'test',
    },
    {
        'variant': 'direct',
        'kernel': 'test',
        'initrd': 'test',
        'loader': 'test',
        'dtb': 'test',
    },
    {
        'variant': 'container',
        'init': '/sbin/init',
    },
    {
        'variant': 'container',
        'init': '/sbin/init',
        'initargs': [
            'test',
        ],
        'initenv': {
            'TEST': '1',
        },
        'initdir': '/',
        'inituser': 'root',
        'initgroup': 'root',
        'idmap': {
            'uid': {
                'target': 0,
                'count': 65536,
            },
            'gid': {
                'target': 0,
                'count': 65536,
            },
        },
    },
    {
        'variant': 'test',
        'arch': 'x86_64',
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
    {
        'variant': 'host',
    },
    {
        'variant': 'host',
        'bootloader': '',
    },
    {
        'variant': 'host',
        'loader': '/nonexistent',
    },
    {
        'variant': 'host',
        'init': '/nonexistent',
    },
    {
        'variant': 'direct',
        'kernel': '',
    },
    {
        'variant': 'direct',
    },
    {
        'variant': 'direct',
        'init': '/nonexistent',
    },
    {
        'variant': 'container',
    },
    {
        'variant': 'container',
        'init': '',
    },
    {
        'variant': 'container',
        'loader': 'test',
    },
    {
        'variant': 'container',
        'kernel': 'test',
    },
    {
        'variant': 'test',
    },
    {
        'variant': 'test',
        'arch': 'x86_64',
        'loader': 'test',
    },
    {
        'variant': 'test',
        'arch': 'x86_64',
        'kernel': 'test',
    },
    {
        'variant': 'test',
        'arch': 'x86_64',
        'init': '/sbin/init',
    },
))
def test_OSInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSInfo dicts.'''
    with pytest.raises(ValidationError):
        OSInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'name': 'platform',
    },
    {
        'name': 'rtc',
        'track': 'boot',
    },
    {
        'name': 'tsc',
        'tickpolicy': 'delay',
    },
    {
        'name': 'hpet',
        'present': 'no',
    },
))
def test_ClockTimerInfo_valid(d: dict) -> None:
    '''Check validation of known-good ClockTimerInfo dicts.'''
    ClockTimerInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'name': '',
    },
    {
        'name': 'rtc',
        'track': 'utc',
    },
    {
        'name': 'tsc',
        'tickpolicy': 'skew',
    },
    {
        'name': 'hpet',
        'present': 'maybe',
    }
))
def test_ClockTimerInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockTimerInfo dicts.'''
    with pytest.raises(ValidationError):
        ClockTimerInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'offset': 'utc',
    },
    {
        'offset': 'localtime',
    },
    {
        'offset': 'timezone',
        'tz': 'America/New_York',
    },
    {
        'offset': 'variable',
        'basis': 'utc',
        'adjustment': '0',
    },
    {
        'offset': 'variable',
        'basis': 'localtime',
        'adjustment': '0',
    },
    {
        'offset': 'absolute',
        'start': 0,
    },
))
def test_ClockInfo_valid(d: dict) -> None:
    '''Check validation of known-good ClockInfo dicts.'''
    ClockInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'offset': '',
    },
    {
        'offset': 'timzeone',
    },
    {
        'offset': 'timezone',
        'tz': '',
    },
    {
        'offset': 'variable',
        'adjustment': '0',
    },
    {
        'offset': 'variable',
        'basis': 'utc',
    },
    {
        'offset': 'variable',
        'basis': '',
        'adjustment': '0',
    },
    {
        'offset': 'variable',
        'basis': 'utc',
        'adjustment': '',
    },
    {
        'offset': 'absolute',
    },
))
def test_ClockInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockInfo dicts.'''
    with pytest.raises(ValidationError):
        ClockInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'state': 'on',
    },
    {
        'state': 'off',
    },
    {
        'state': 'on',
        'retries': 4096,
    },
))
def test_FeaturesHyperVSpinlocks_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVSpinlocks dicts.'''
    FeaturesHyperVSpinlocks.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'retries': 4096,
    },
    {
        'state': 'on',
        'retries': 0,
    },
    {
        'state': '',
    },
))
def test_FeaturesHyperVSpinlocks_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVSpinlocks dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVSpinlocks.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'state': 'on',
    },
    {
        'state': 'off',
    },
    {
        'state': 'on',
        'direct': 'on',
    },
    {
        'state': 'on',
        'direct': 'off',
    },
))
def test_FeaturesHyperVSTimer_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVSTimer dicts.'''
    FeaturesHyperVSTimer.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'state': '',
    },
    {
        'state': 'on',
        'direct': '',
    },
))
def test_FeaturesHyperVSTimer_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVSTimer dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVSTimer.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'state': 'on',
    },
    {
        'state': 'off',
    },
    {
        'state': 'on',
        'value': 'test',
    },
))
def test_FeaturesHyperVVendorID_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVVendorID dicts.'''
    FeaturesHyperVVendorID.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'state': '',
    },
    {
        'state': 'on',
        'value': '',
    },
    {
        'state': 'on',
        'value': 'verylongvendorid',
    },
))
def test_FeaturesHyperVVendorID_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVVendorID dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVVendorID.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'mode': 'passthrough',
    },
    {
        'mode': 'custom',
    },
    {
        'avic': 'on',
        'evmcs': 'on',
        'frequencies': 'on',
        'ipi': 'on',
        'reenlightenment': 'on',
        'relaxed': 'on',
        'reset': 'on',
        'runtime': 'on',
        'synic': 'on',
        'tlbflush': 'on',
        'vapic': 'on',
        'vpindex': 'on',
        'spinlocks': {
            'state': 'on',
        },
        'stimer': {
            'state': 'on',
        },
        'vendor_id': {
            'state': 'on',
            'value': 'test',
        },
    },
    {
        'avic': 'off',
        'evmcs': 'off',
        'frequencies': 'off',
        'ipi': 'off',
        'reenlightenment': 'off',
        'relaxed': 'off',
        'reset': 'off',
        'runtime': 'off',
        'synic': 'off',
        'tlbflush': 'off',
        'vapic': 'off',
        'vpindex': 'off',
        'spinlocks': {
            'state': 'off',
        },
        'stimer': {
            'state': 'off',
        },
        'vendor_id': {
            'state': 'off',
        },
    },
))
def test_FeaturesHyperVInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVInfo dicts.'''
    FeaturesHyperVInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'mode': '',
    },
))
def test_FeaturesHyperVInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'state': 'on',
    },
    {
        'state': 'off',
    },
    {
        'state': 'on',
        'size': 1024,
    },
    {
        'state': 'on',
        'size': 65536,
    },
))
def test_FeaturesKVMDirtyRing_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesKVMDirtyRing dicts.'''
    FeaturesKVMDirtyRing.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'state': '',
    },
    {
        'state': 'on',
        'size': 0,
    },
    {
        'state': 'on',
        'size': 256,
    },
    {
        'state': 'on',
        'size': 131072,
    },
    {
        'state': 'on',
        'size': 5000,
    },
))
def test_FeaturesKVMDirtyRing_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesKVMDirtyRing dicts.'''
    with pytest.raises(ValidationError):
        FeaturesKVMDirtyRing.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'dirty_ring': {
            'state': 'on',
        },
        'hidden': 'on',
        'hint_dedicated': 'on',
        'poll_control': 'on',
        'pv_ipi': 'on',
    },
    {
        'dirty_ring': {
            'state': 'off',
        },
        'hidden': 'off',
        'hint_dedicated': 'off',
        'poll_control': 'off',
        'pv_ipi': 'off',
    },
))
def test_FeaturesKVMInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesKVMInfo dicts.'''
    FeaturesKVMInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'hidden': '',
    },
    {
        'hint_dedicated': '',
    },
    {
        'poll_control': '',
    },
    {
        'pv_ipi': '',
    },
))
def test_FeaturesKVMInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesKVMInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesKVMInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'state': 'on',
    },
    {
        'state': 'off',
    },
    {
        'state': 'on',
        'mode': 'sync_pt',
    },
    {
        'state': 'on',
        'mode': 'share_pt',
    },
))
def test_FeaturesXenPassthrough_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesXenPassthrough dicts.'''
    FeaturesXenPassthrough.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'state': '',
    },
    {
        'state': 'on',
        'mode': '',
    },
))
def test_FeaturesXenPassthrough_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesXenPassthrough dicts.'''
    with pytest.raises(ValidationError):
        FeaturesXenPassthrough.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'e820_host': 'on',
        'passthrough': {
            'state': 'on',
        },
    },
    {
        'e820_host': 'off',
        'passthrough': {
            'state': 'off',
        },
    },
))
def test_FeaturesXenInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesXenInfo dicts.'''
    FeaturesXenInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'e820_host': '',
    },
))
def test_FeaturesXenInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesXenInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesXenInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'tb_cache': 128,
    },
))
def test_FeaturesTCGInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesTCGInfo dicts.'''
    FeaturesTCGInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'tb_cache': 0,
    },
))
def test_FeaturesTCGInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesTCGInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesTCGInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'eoi': 'on',
    },
    {
        'eoi': 'off',
    },
))
def test_FeaturesAPICInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesAPICInfo dicts.'''
    FeaturesAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'eoi': '',
    },
))
def test_FeaturesAPICInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesAPICInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'version': '2',
    },
    {
        'version': '3',
    },
    {
        'version': 'host',
    },
    {
        'version': 2,
    },
    {
        'version': 3,
    },
))
def test_FeaturesGICInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesGICInfo dicts.'''
    FeaturesGICInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'version': '',
    },
    {
        'version': 0,
    },
))
def test_FeaturesGICInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesGICInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesGICInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'driver': 'kvm',
    },
    {
        'driver': 'qemu',
    },
))
def test_FeaturesIOAPICInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesIOAPICInfo dicts.'''
    FeaturesIOAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'driver': '',
    },
))
def test_FeaturesIOAPICInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesIOAPICInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesIOAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'policy': 'allow',
    },
    {
        'policy': 'deny',
    },
    {
        'policy': 'default',
    },
    {
        'policy': 'deny',
        'modify': dict(),
    },
    {
        'policy': 'default',
        'modify': {
            'mknod': 'on',
            'dac_override': 'off',
        },
    },
))
def test_FeaturesCapabilities_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesCapabilities dicts.'''
    FeaturesCapabilities.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'policy': '',
    },
    {
        'policy': 'none',
    },
    {
        'policy': 'deny',
        'modify': {
            'mknod': '',
        },
    },
))
def test_FeaturesCapabilities_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesCapabilities dicts.'''
    with pytest.raises(ValidationError):
        FeaturesCapabilities.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'acpi': True,
        'apic': dict(),
        'async_teardown': 'on',
        'caps': {
            'policy': 'allow',
        },
        'gic': dict(),
        'hap': 'on',
        'htm': 'on',
        'hyperv': dict(),
        'kvm': dict(),
        'pae': True,
        'pmu': 'on',
        'pvspinlock': 'on',
        'smm': 'on',
        'tcg': dict(),
        'vmcoreinfo': 'on',
        'vmport': 'on',
        'xen': dict(),
    },
    {
        'acpi': False,
        'apic': {
            'eoi': 'off',
        },
        'async_teardown': 'off',
        'caps': {
            'policy': 'allow',
        },
        'gic': {
            'version': 'host',
        },
        'hap': 'off',
        'htm': 'off',
        'hyperv': {
            'mode': 'passthrough',
        },
        'kvm': {
            'hidden': 'on',
        },
        'pae': False,
        'pmu': 'off',
        'pvspinlock': 'off',
        'smm': 'off',
        'tcg': {
            'tb_cache': 256,
        },
        'vmcoreinfo': 'off',
        'vmport': 'off',
        'xen': {
            'passthrough': {
                'state': 'off',
            },
        },
    },
))
def test_FeaturesInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesInfo dicts.'''
    FeaturesInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'acpi': '',
    },
    {
        'pae': '',
    },
    {
        'async_teardown': '',
    },
    {
        'hap': '',
    },
    {
        'htm': '',
    },
    {
        'pmu': '',
    },
    {
        'pvspinlock': '',
    },
    {
        'smm': '',
    },
    {
        'vmcoreinfo': '',
    },
    {
        'vmport': '',
    },
))
def test_FeaturesInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'queues': 8,
    },
    {
        'cmd_per_lun': 8,
    },
    {
        'max_sectors': 64,
    },
))
def test_ControllerDriverInfo_valid(d: dict) -> None:
    '''Check validation of known-good ControllerDriverInfo dicts.'''
    ControllerDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'queues': '',
    },
    {
        'cmd_per_lun': '',
    },
    {
        'max_sectors': '',
    },
    {
        'queues': 0,
    },
    {
        'cmd_per_lun': 0,
    },
    {
        'max_sectors': 0,
    },
))
def test_ControllerDriverInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ControllerDriverInfo dicts.'''
    with pytest.raises(ValidationError):
        ControllerDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'scsi',
    },
    {
        'type': 'scsi',
        'index': 0,
    },
    {
        'type': 'scsi',
        'model': 'virtio',
    },
    {
        'type': 'usb',
        'model': 'qemu-xhci',
        'ports': 4,
    },
    {
        'type': 'virtio-serial',
        'ports': 4,
        'vectors': 4,
    },
    {
        'type': 'xenbus',
        'maxGrantFrames': 4,
        'maxEventChannels': 4,
    },
    {
        'type': 'scsi',
        'driver': {
            'queues': 8,
        },
    },
))
def test_ControllerDevice_valid(d: dict) -> None:
    '''Check validation of known-good ControllerDevice dicts.'''
    ControllerDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'scsi',
        'index': -1,
    },
    {
        'type': 'scsi',
        'model': '',
    },
    {
        'type': 'usb',
        'ports': -1,
    },
    {
        'type': 'virtio-serial',
        'ports': 1,
        'vectors': -1,
    },
    {
        'type': 'xenbus',
        'maxEventChannels': -1,
    },
    {
        'type': 'xenbus',
        'maxGrantFrames': -1,
    },
    {
        'type': 'xenbus',
        'driver': dict(),
    },
))
def test_ControllerDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad ControllerDevice dicts.'''
    with pytest.raises(ValidationError):
        ControllerDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'pool': 'test',
        'volume': 'test',
    },
))
def test_DiskVolumeSrcInfo_valid(d: dict) -> None:
    '''Check validation of known-good DiskVolumeSrcInfo dicts.'''
    DiskVolumeSrcInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'pool': 'test',
    },
    {
        'volume': 'test',
    },
))
def test_DiskVolumeSrcInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad DiskVolumeSrcInfo dicts.'''
    with pytest.raises(ValidationError):
        DiskVolumeSrcInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'dev': '/dev/sda',
    },
    {
        'dev': '/dev/sda',
        'bus': 'scsi',
        'addr': {
            'bus': 0,
            'target': 0,
            'unit': 0,
        },
    },
    {
        'dev': '/dev/vda',
        'bus': 'virtio',
        'addr': {
            'bus': '0x00',
            'slot': '0x00',
            'function': '0x0',
        },
    },
    {
        'dev': '/dev/sda',
        'removable': 'on',
    },
    {
        'dev': '/dev/sda',
        'removable': 'off',
    },
    {
        'dev': '/dev/sda',
        'rotation_rate': 1,
    },
    {
        'dev': '/dev/sda',
        'rotation_rate': 1025,
    },
    {
        'dev': '/dev/sda',
        'rotation_rate': 65534,
    },
))
def test_DiskTargetInfo_valid(d: dict) -> None:
    '''Check validation of known-good DiskTargetInfo dicts.'''
    DiskTargetInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'dev': '/dev/vda',
        'bus': 'scsi',
        'addr': {
            'bus': '0x00',
            'slot': '0x00',
            'function': '0x0',
        },
    },
    {
        'dev': '/dev/sda',
        'bus': 'virtio',
        'addr': {
            'bus': 0,
            'target': 0,
            'unit': 0,
        },
    },
    {
        'dev': '/dev/sda',
        'removable': '',
    },
    {
        'dev': '/dev/sda',
        'rotation_rate': 0,
    },
    {
        'dev': '/dev/sda',
        'rotation_rate': 65536,
    },
))
def test_DiskTargetInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad DiskTargetInfo dicts.'''
    with pytest.raises(ValidationError):
        DiskTargetInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'volume',
        'src': {
            'pool': 'test',
            'volume': 'test',
        },
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'block',
        'src': '/dev/sda',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'boot': 1,
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'device': 'disk',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'device': 'cdrom',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'device': 'floppy',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'device': 'lun',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'readonly': True,
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'readonly': False,
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'snapshot': 'internal',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'snapshot': 'external',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'snapshot': 'manual',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'snapshot': 'no',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'startup': 'mandatory',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'startup': 'requisite',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'startup': 'optional',
    },
))
def test_DiskDevice_valid(d: dict) -> None:
    '''Check validation of known-good DiskDevice dicts.'''
    DiskDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'file',
        'src': '',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'file',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'file',
        'src': '/nonexistent',
    },
    {
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'file',
        'src': {
            'pool': 'test',
            'volume': 'test',
        },
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'volume',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'boot': 0,
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'device': '',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'readonly': '',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'snapshot': '',
    },
    {
        'type': 'file',
        'src': '/nonexistent',
        'target': {
            'dev': '/dev/sda',
        },
        'startup': '',
    },
    {
        'type': 'block',
        'src': '/dev/sda',
        'target': {
            'dev': '/dev/sda',
        },
        'startup': 'requisite',
    },
))
def test_DiskDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad DiskDevice dicts.'''
    with pytest.raises(ValidationError):
        DiskDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'path',
    },
    {
        'type': 'path',
        'wrpolicy': 'immediate',
    },
    {
        'type': 'loop',
        'format': 'raw',
    },
    {
        'type': 'virtiofs',
        'queues': 8,
    },
))
def test_FilesystemDriverInfo_valid(d: dict) -> None:
    '''Check validation of known-good FilesystemDriverInfo dicts.'''
    FilesystemDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'path',
        'wrpolicy': '',
    },
    {
        'type': 'loop',
        'format': '',
    },
    {
        'type': 'virtiofs',
        'queues': 0,
    },
))
def test_FilesystemDriverInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FilesystemDriverInfo dicts.'''
    with pytest.raises(ValidationError):
        FilesystemDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'accessmode': 'mapped',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'accessmode': 'passthrough',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'accessmode': 'squash',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'dmode': '0775',
        'fmode': '0644',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'driver': {
            'type': 'path',
        },
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'multidev': 'default',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'multidev': 'remap',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'multidev': 'forbid',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'multidev': 'warn',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'readonly': True,
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'readonly': False,
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'src_type': 'socket',
    },
))
def test_Filesystem_valid(d: dict) -> None:
    '''Check validation of known-good Filesystem dicts.'''
    Filesystem.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
        'source': '/nonexistent',
        'target': '/',
    },
    {
        'type': 'mount',
        'source': '',
        'target': '/',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'accessmode': '',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'dmode': '',
        'fmode': '0644',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'dmode': '0775',
        'fmode': '',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'driver': '',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'multidev': '',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'readonly': '',
    },
    {
        'type': 'mount',
        'source': '/nonexistent',
        'target': '/',
        'src_type': '',
    },
))
def test_Filesystem_invalid(d: dict) -> None:
    '''Check validation of known-bad Filesystem dicts.'''
    with pytest.raises(ValidationError):
        Filesystem.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'instanceid': 'test',
    },
    {
        'type': 'openvswitch',
        'interfaceid': 'test',
        'profileid': 'test',
    },
    {
        'type': '802.1Qbg',
        'managerid': 'test',
        'instanceid': 'test',
        'typeid': 'test',
        'typeidversion': 'test',
    },
    {
        'type': '802.1Qbh',
        'profileid': 'test',
    },
))
def test_NetworkVPort_valid(d: dict) -> None:
    '''Check validation of known-good NetworkVPort dicts.'''
    NetworkVPort.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'instanceid': '',
    },
    {
        'type': '',
        'interfaceid': 'test',
        'profileid': 'test',
    },
    {
        'type': 'openvswitch',
        'interfaceid': '',
        'profileid': 'test',
    },
    {
        'type': 'openvswitch',
        'interfaceid': 'test',
        'profileid': '',
    },
    {
        'type': '802.1Qbg',
        'managerid': '',
        'instanceid': 'test',
        'typeid': 'test',
        'typeidversion': 'test',
    },
    {
        'type': '802.1Qbg',
        'managerid': 'test',
        'instanceid': '',
        'typeid': 'test',
        'typeidversion': 'test',
    },
    {
        'type': '802.1Qbg',
        'managerid': 'test',
        'instanceid': 'test',
        'typeid': '',
        'typeidversion': 'test',
    },
    {
        'type': '802.1Qbg',
        'managerid': 'test',
        'instanceid': 'test',
        'typeid': 'test',
        'typeidversion': '',
    },
    {
        'type': '802.1Qbh',
        'profileid': '',
    },
    {
        'type': '',
        'profileid': 'test',
    },
))
def test_NetworkVPort_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkVPort dicts.'''
    with pytest.raises(ValidationError):
        NetworkVPort.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'address': '192.0.2.1',
        'prefix': 24,
    },
    {
        'address': '2001:db8::1',
        'prefix': 32,
    },
))
def test_NetworkIPInfo_valid(d: dict) -> None:
    '''Check validation of known-good NetworkIPInfo dicts.'''
    NetworkIPInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'address': '',
        'prefix': 24,
    },
    {
        'address': '192.0.2.1',
        'prefix': 0,
    },
    {
        'address': '2001:db8::1',
        'prefix': 0,
    },
    {
        'address': '192.0.2.1',
        'prefix': 32,
    },
    {
        'address': '2001:db8::1',
        'prefix': 128,
    },
))
def test_NetworkIPInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkIPInfo dicts.'''
    with pytest.raises(ValidationError):
        NetworkIPInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'network',
    },
    {
        'type': 'network',
        'src': 'test',
    },
    {
        'type': 'network',
        'target': 'test',
    },
    {
        'type': 'network',
        'mac': '02:00:00:00:00:01',
    },
    {
        'type': 'network',
        'boot': 1,
    },
    {
        'type': 'network',
        'virtualport': {
            'instanceid': 'test',
        },
    },
    {
        'type': 'bridge',
    },
    {
        'type': 'bridge',
        'virtualport': {
            'type': 'openvswitch',
            'interfaceid': 'test',
            'profileid': 'test',
        },
    },
    {
        'type': 'direct',
        'mode': 'vepa',
    },
    {
        'type': 'direct',
        'mode': 'bridge',
    },
    {
        'type': 'direct',
        'mode': 'private',
    },
    {
        'type': 'direct',
        'mode': 'passthrough',
    },
    {
        'type': 'user',
    },
    {
        'type': 'user',
        'ipv4': {
            'address': '192.0.2.1',
            'prefix': 24,
        },
    },
    {
        'type': 'user',
        'ipv6': {
            'address': '2001:db8::1',
            'prefix': 32,
        },
    },
    {
        'type': 'user',
        'ipv4': {
            'address': '192.0.2.1',
            'prefix': 24,
        },
        'ipv6': {
            'address': '2001:db8::1',
            'prefix': 32,
        },
    },
))
def test_NetworkInterface_valid(d: dict) -> None:
    '''Check validation of known-good NetworkInterface dicts.'''
    NetworkInterface.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'network',
        'src': '',
    },
    {
        'type': 'network',
        'target': '',
    },
    {
        'type': 'network',
        'mac': '',
    },
    {
        'type': 'network',
        'mac': '02:00:00:00:00:0z',
    },
    {
        'type': 'network',
        'boot': 0,
    },
    {
        'type': 'direct',
        'mode': '',
    },
    {
        'type': 'direct',
    },
    {
        'type': 'network',
        'mode': 'passthrough',
    },
    {
        'type': 'user',
        'ipv4': '',
    },
    {
        'type': 'user',
        'ipv6': '',
    },
    {
        'type': 'network',
        'ipv4': {
            'address': '192.0.2.1',
            'prefix': 24,
        },
    },
    {
        'type': 'network',
        'ipv6': {
            'address': '2001:db8::1',
            'prefix': 32,
        },
    },
))
def test_NetworkInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkInterface dicts.'''
    with pytest.raises(ValidationError):
        NetworkInterface.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'dev': '/dev/input/event1',
    },
    {
        'dev': '/dev/input/event1',
        'grab': 'all',
    },
    {
        'dev': '/dev/input/event1',
        'repeat': 'on',
    },
    {
        'dev': '/dev/input/event1',
        'repeat': 'off',
    },
    {
        'dev': '/dev/input/event1',
        'grabToggle': 'ctrl-ctrl',
    },
))
def test_InputSource_valid(d: dict) -> None:
    '''Check validation of known-good InputSource dicts.'''
    InputSource.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'dev': '',
    },
    {
        'dev': '/dev/input/event1',
        'grab': '',
    },
    {
        'dev': '/dev/input/event1',
        'repeat': '',
    },
    {
        'dev': '/dev/input/event1',
        'grabToggle': '',
    },
))
def test_InputSource_invalid(d: dict) -> None:
    '''Check validation of known-bad InputSource dicts.'''
    with pytest.raises(ValidationError):
        InputSource.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'keyboard',
    },
    {
        'type': 'mouse',
    },
    {
        'type': 'tablet',
    },
    {
        'type': 'keyboard',
        'bus': 'usb',
    },
    {
        'type': 'keyboard',
        'bus': 'ps2',
    },
    {
        'type': 'keyboard',
        'bus': 'virtio',
    },
    {
        'type': 'keyboard',
        'bus': 'xen',
    },
    {
        'type': 'keyboard',
        'bus': 'virtio',
        'model': 'virtio',
    },
    {
        'type': 'passthrough',
        'src': {
            'dev': '/dev/input/event1',
        },
    },
    {
        'type': 'evdev',
        'src': {
            'dev': '/dev/input/event1',
        },
    },
))
def test_InputDevice_valid(d: dict) -> None:
    '''Check validation of known-good InputDevice dicts.'''
    InputDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'keyboard',
        'bus': '',
    },
    {
        'type': 'keyboard',
        'bus': 'virtio',
        'model': '',
    },
    {
        'type': 'keyboard',
        'src': {
            'dev': '/dev/input/event1',
        },
    },
    {
        'type': 'evdev',
    },
))
def test_InputDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad InputDevice dicts.'''
    with pytest.raises(ValidationError):
        InputDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'none',
    },
    {
        'type': 'address',
        'address': '192.0.2.1',
    },
    {
        'type': 'address',
        'address': '2001:db8::1',
    },
    {
        'type': 'network',
        'network': 'test',
    },
    {
        'type': 'socket',
        'socket': '/tmp/test.sock',
    },
))
def test_GraphicsListener_valid(d: dict) -> None:
    '''Check validation of known-good GraphicsListener dicts.'''
    GraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': 'none',
        'address': '192.0.2.1',
    },
    {
        'type': 'none',
        'network': 'test',
    },
    {
        'type': 'none',
        'socket': '/tmp/test.sock',
    },
    {
        'type': 'address',
    },
    {
        'type': 'address',
        'network': 'test',
    },
    {
        'type': 'address',
        'socket': '/tmp/test.sock',
    },
    {
        'type': 'network',
    },
    {
        'type': 'network',
        'address': '192.0.2.1',
    },
    {
        'type': 'network',
        'socket': '/tmp/test.sock',
    },
    {
        'type': 'socket',
    },
    {
        'type': 'socket',
        'address': '192.0.2.1',
    },
    {
        'type': 'socket',
        'network': 'test',
    },
))
def test_GraphicsListener_invalid(d: dict) -> None:
    '''Check validation of known-bad GraphicsListener dicts.'''
    with pytest.raises(ValidationError):
        GraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'vnc',
    },
    {
        'type': 'spice',
    },
    {
        'type': 'rdp',
    },
    {
        'type': 'vnc',
        'listeners': [
            {
                'type': 'none',
            },
        ],
    },
    {
        'type': 'vnc',
        'port': 5900,
    },
    {
        'type': 'vnc',
        'autoport': 'yes',
    },
    {
        'type': 'vnc',
        'port': 5900,
        'autoport': 'no',
    },
    {
        'type': 'vnc',
        'websocket': 5900,
    },
    {
        'type': 'vnc',
        'socket': '/run/vnc.sock',
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
        'passwdValidTo': '2023-12-31T00:00:00',
    },
    {
        'type': 'vnc',
        'keymap': 'us',
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
        'connected': 'keep',
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
        'connected': 'disconnect',
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
        'connected': 'fail',
    },
    {
        'type': 'vnc',
        'sharePolicy': 'allow-exclusive',
    },
    {
        'type': 'vnc',
        'sharePolicy': 'force-shared',
    },
    {
        'type': 'vnc',
        'sharePolicy': 'ignore',
    },
    {
        'type': 'vnc',
        'powerControl': 'yes',
    },
    {
        'type': 'vnc',
        'powerControl': 'no',
    },
    {
        'type': 'spice',
        'tlsPort': 5900,
    },
    {
        'type': 'spice',
        'defaltMode': 'secure',
    },
    {
        'type': 'spice',
        'defaltMode': 'insecure',
    },
    {
        'type': 'spice',
        'defaltMode': 'any',
    },
    {
        'type': 'spice',
        'channels': dict(),
    },
    {
        'type': 'spice',
        'channels': {
            'main': 'secure',
            'record': 'insecure',
        },
    },
    {
        'type': 'rdp',
        'multiUser': 'yes',
    },
    {
        'type': 'rdp',
        'multiUser': 'no',
    },
    {
        'type': 'rdp',
        'multiUser': 'yes',
        'replaceUser': 'yes',
    },
    {
        'type': 'rdp',
        'multiUser': 'yes',
        'replaceUser': 'no',
    },
))
def test_GraphicsDevice_valid(d: dict) -> None:
    '''Check validation of known-good GraphicsDevice dicts.'''
    GraphicsDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'vnc',
        'port': -1,
    },
    {
        'type': 'vnc',
        'port': 0,
    },
    {
        'type': 'vnc',
        'port': 65536,
    },
    {
        'type': 'vnc',
        'autoport': '',
    },
    {
        'type': 'vnc',
        'socket': '',
    },
    {
        'type': 'vnc',
        'websocket': -2,
    },
    {
        'type': 'vnc',
        'websocket': 65536,
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
        'passwdValidTo': '',
    },
    {
        'type': 'vnc',
        'passwdValidTo': '2023-12-31T00:00:00',
    },
    {
        'type': 'vnc',
        'keymap': '',
    },
    {
        'type': 'vnc',
        'connected': 'keep',
    },
    {
        'type': 'vnc',
        'passwd': 'secret',
        'connected': '',
    },
    {
        'type': 'vnc',
        'sharePolicy': '',
    },
    {
        'type': 'vnc',
        'powerControl': '',
    },
    {
        'type': 'spice',
        'tlsPort': 0,
    },
    {
        'type': 'spice',
        'tlsPort': 65536,
    },
    {
        'type': 'spice',
        'defaultMode': '',
    },
    {
        'type': 'spice',
        'channels': [],
    },
    {
        'type': 'spice',
        'channels': {
            'main': '',
        },
    },
    {
        'type': 'rdp',
        'multiUser': '',
    },
    {
        'type': 'rdp',
        'replaceUser': 'yes',
    },
    {
        'type': 'rdp',
        'multiUser': 'yes',
        'replaceUser': '',
    },
))
def test_GraphicsDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad GraphicsDevice dicts.'''
    with pytest.raises(ValidationError):
        GraphicsDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'vga',
    },
    {
        'type': 'cirrus',
    },
    {
        'type': 'vmvga',
    },
    {
        'type': 'xen',
    },
    {
        'type': 'vbox',
    },
    {
        'type': 'virtio',
    },
    {
        'type': 'qxl',
    },
    {
        'type': 'gop',
    },
    {
        'type': 'bochs',
    },
    {
        'type': 'ramfb',
    },
    {
        'type': 'none',
    },
    {
        'type': 'vga',
        'vram': 1024,
    },
    {
        'type': 'vga',
        'vram': 65536,
    },
    {
        'type': 'vga',
        'vram': 4194304,
    },
    {
        'type': 'vga',
        'heads': 4,
    },
    {
        'type': 'virtio',
        'blob': 'on',
    },
    {
        'type': 'virtio',
        'blob': 'off',
    },
))
def test_VideoDevice_valid(d: dict) -> None:
    '''Check validation of known-good VideoDevice dicts.'''
    VideoDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'vga',
        'vram': 0,
    },
    {
        'type': 'vga',
        'vram': 2000,
    },
    {
        'type': 'vga',
        'heads': 0,
    },
    {
        'type': 'vga',
        'blob': 'on',
    },
    {
        'type': 'virtio',
        'blob': '',
    },
))
def test_VideoDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad VideoDevice dicts.'''
    with pytest.raises(ValidationError):
        VideoDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'path': '/nonexistent',
    },
    {
        'path': '/run/char.sock',
        'mode': 'bind',
    },
    {
        'path': '/run/char.sock',
        'mode': 'connect',
    },
    {
        'channel': 'org.qemu.console.serial.0',
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
        'service': 23,
    },
    {
        'host': 'console.example.com',
        'mode': 'bind',
        'service': 23,
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
        'service': 23,
        'tls': 'no',
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
        'service': 23,
        'tls': 'yes',
    },
))
def test_CharDevSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevSource dicts.'''
    CharDevSource.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'path': '',
    },
    {
        'path': '/run/char.sock',
        'mode': '',
    },
    {
        'path': '/nonexistent',
        'channel': 'org.qemu.console.serial.0',
    },
    {
        'host': 'console.example.com',
        'service': 23,
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
        'service': 0,
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
        'service': 65536,
    },
    {
        'host': 'console.example.com',
        'mode': 'connect',
        'service': 23,
        'tls': '',
    },
    {
        'path': '/nonexistent',
        'service': 23,
    },
    {
        'path': '/nonexistent',
        'tls': 'yes',
    },
    {
        'channel': 'org.qemu.console.serial.0',
        'mode': 'connect',
    },
))
def test_CharDevSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevSource.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'port': 0,
    },
    {
        'port': 0,
        'type': 'virtio',
    },
    {
        'type': 'guestfwd',
        'address': '192.0.2.1',
        'port': 80,
    },
    {
        'type': 'guestfwd',
        'address': '2001:db8::1',
        'port': 80,
    },
    {
        'name': 'org.qemu.guest_agent.0',
    },
    {
        'type': 'virtio',
        'name': 'org.qemu.guest_agent.0',
    },
    {
        'name': 'org.qemu.guest_agent.0',
        'state': 'connected',
    },
))
def test_CharDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good CharDevTarget dicts.'''
    CharDevTarget.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'port': -1,
    },
    {
        'port': 0,
        'name': 'test',
    },
    {
        'port': 0,
        'state': 'connected',
    },
    {
        'type': 'guestfwd',
        'address': '192.0.2.1',
    },
    {
        'address': '192.0.2.1',
        'port': 80,
    },
    {
        'type': 'virtio',
        'address': '192.0.2.1',
        'port': 80,
    },
    {
        'type': 'guestfwd',
        'address': '192.0.2.1',
        'port': 0,
    },
    {
        'type': 'guestfwd',
        'address': '192.0.2.1',
        'port': 65536,
    },
    {
        'type': 'guestfwd',
        'address': '192.0.2.1',
        'port': 80,
        'name': 'test',
    },
    {
        'type': 'guestfwd',
        'address': '192.0.2.1',
        'port': 80,
        'state': 'connected',
    },
    {
        'name': '',
    },
))
def test_CharDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevTarget dicts.'''
    with pytest.raises(ValidationError):
        CharDevTarget.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'file': '/var/log/domain.log',
    },
    {
        'file': '/var/log/domain.log',
        'append': 'on',
    },
    {
        'file': '/var/log/domain.log',
        'append': 'off',
    },
))
def test_CharDevLog_valid(d: dict) -> None:
    '''Check validation of known-good CharDevLog dicts.'''
    CharDevLog.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'file': '',
    },
    {
        'file': '/var/log/domain.log',
        'append': '',
    },
))
def test_CharDevLog_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevLog dicts.'''
    with pytest.raises(ValidationError):
        CharDevLog.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'category': 'serial',
        'type': 'null',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'parallel',
        'type': 'null',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'console',
        'type': 'null',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'channel',
        'type': 'null',
        'target': {
            'name': 'org.qemu.guest_agent.0',
        },
    },
    {
        'category': 'serial',
        'type': 'null',
        'target': {
            'port': 0,
        },
        'log': {
            'file': '/var/log/domain.log',
        },
    },
    {
        'category': 'serial',
        'type': 'stdio',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'vc',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'file',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'pipe',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'nmdm',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'pty',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'pty',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'tcp',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'unix',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
            'mode': 'bind',
        },
    },
    {
        'category': 'serial',
        'type': 'spiceport',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
))
def test_CharacterDevice_valid(d: dict) -> None:
    '''Check validation of known-good CharacterDevice dicts.'''
    CharacterDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'category': '',
        'type': 'null',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': '',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'null',
        'target': {
            'port': 0,
        },
        'log': dict(),
    },
    {
        'category': 'serial',
        'type': 'null',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'stdio',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'vc',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'file',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'file',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'file',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'dev',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'nmdm',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'nmdm',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'nmdm',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'pty',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'pty',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'tcp',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'tcp',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'tcp',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'unix',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
    {
        'category': 'serial',
        'type': 'unix',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'unix',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'unix',
        'target': {
            'port': 0,
        },
        'src': {
            'channel': 'org.qemu.console.serial.0',
        },
    },
    {
        'category': 'serial',
        'type': 'spiceport',
        'target': {
            'port': 0,
        },
    },
    {
        'category': 'serial',
        'type': 'spiceport',
        'target': {
            'port': 0,
        },
        'src': {
            'host': '192.0.2.1',
            'service': 80,
            'mode': 'connect',
        },
    },
    {
        'category': 'serial',
        'type': 'spiceport',
        'target': {
            'port': 0,
        },
        'src': {
            'path': '/nonexistent',
        },
    },
))
def test_CharacterDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad CharacterDevice dicts.'''
    with pytest.raises(ValidationError):
        CharacterDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'model': 'itco',
    },
    {
        'model': 'i6300esb',
    },
    {
        'model': 'ib700',
    },
    {
        'model': 'diag288',
    },
    {
        'model': 'i6300esb',
        'action': 'reset',
    },
    {
        'model': 'i6300esb',
        'action': 'shutdown',
    },
    {
        'model': 'i6300esb',
        'action': 'poweroff',
    },
    {
        'model': 'i6300esb',
        'action': 'pause',
    },
    {
        'model': 'i6300esb',
        'action': 'none',
    },
    {
        'model': 'i6300esb',
        'action': 'dump',
    },
    {
        'model': 'i6300esb',
        'action': 'inject-nmi',
    },
))
def test_WatchdogDevice_valid(d: dict) -> None:
    '''Check validation of known-good WatchdogDevice dicts.'''
    WatchdogDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'model': '',
    },
    {
        'model': 'i6300esb',
        'action': '',
    },
))
def test_WatchdogDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad WatchdogDevice dicts.'''
    with pytest.raises(ValidationError):
        WatchdogDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'model': 'builtin',
    },
    {
        'model': 'random',
        'path': '/dev/urandom',
    },
    {
        'model': 'egd',
        'type': 'unix',
        'path': '/run/egd.sock',
        'mode': 'connect',
    },
    {
        'model': 'egd',
        'type': 'tcp',
        'host': '192.0.2.1',
        'service': 1000,
        'mode': 'connect',
    },
))
def test_RNGBackend_valid(d: dict) -> None:
    '''Check validation of known-good RNGBackend dicts.'''
    RNGBackend.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'model': '',
    },
    {
        'model': 'random',
    },
    {
        'model': 'egd',
    },
))
def test_RNGBackend_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGBackend dicts.'''
    with pytest.raises(ValidationError):
        RNGBackend.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'model': 'virtio',
    },
    {
        'model': 'virtio',
        'rate': {
            'bytes': 65536,
            'period': 1000,
        },
    },
    {
        'model': 'virtio',
        'backend': {
            'model': 'builtin',
        },
    },
))
def test_RNGDevice_valid(d: dict) -> None:
    '''Check validation of known-good RNGDevice dicts.'''
    RNGDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'model': '',
    },
    {
        'model': 'virtio',
        'rate': dict(),
    },
    {
        'model': 'virtio',
        'backend': '',
    },
))
def test_RNGDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGDevice dicts.'''
    with pytest.raises(ValidationError):
        RNGDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'type': 'emulator',
    },
    {
        'type': 'emulator',
        'model': 'tpm-tis',
    },
    {
        'type': 'emulator',
        'model': 'tpm-crb',
    },
    {
        'type': 'emulator',
        'model': 'tpm-spapr',
    },
    {
        'type': 'emulator',
        'model': 'tpm-spapr-proxy',
    },
    {
        'type': 'passthrough',
        'dev': '/dev/tpm0',
    },
    {
        'type': 'emulator',
        'encryption': '65267a83-2c8c-42e3-95e2-ae9a1fe522a7',
    },
    {
        'type': 'emulator',
        'version': '1.2',
    },
    {
        'type': 'emulator',
        'version': '2.0',
    },
    {
        'type': 'emulator',
        'persistent_state': 'yes',
    },
    {
        'type': 'emulator',
        'persistent_state': 'no',
    },
    {
        'type': 'emulator',
        'active_pcr_banks': [],
    },
    {
        'type': 'emulator',
        'active_pcr_banks': [
            'sha256',
        ],
    },
))
def test_TPMDevice_valid(d: dict) -> None:
    '''Check validation of known-good TPMDevice dicts.'''
    TPMDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'type': '',
    },
    {
        'type': 'passthrough',
    },
    {
        'type': 'emulator',
        'model': '',
    },
    {
        'type': 'passthrough',
        'dev': '',
    },
    {
        'type': 'emulator',
        'encryption': '',
    },
    {
        'type': 'emulator',
        'version': '',
    },
    {
        'type': 'emulator',
        'persistent_state': '',
    },
))
def test_TPMDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad TPMDevice dicts.'''
    with pytest.raises(ValidationError):
        TPMDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'model': 'virtio',
    },
))
def test_SimpleDevice_valid(d: dict) -> None:
    '''Check validation of known-good SimpleDevice dicts.'''
    SimpleDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
    {
        'model': '',
    },
))
def test_SimpleDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad SimpleDevice dicts.'''
    with pytest.raises(ValidationError):
        SimpleDevice.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
))
def test_Devices_valid(d: dict) -> None:
    '''Check validation of known-good Devices dicts.'''
    Devices.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'controllers': [
            {
                'type': 'usb',
                'index': 0,
            },
            {
                'type': 'usb',
                'index': 0,
            },
        ],
    },
))
def test_Devices_invalid(d: dict) -> None:
    '''Check validation of known-bad Devices dicts.'''
    with pytest.raises(ValidationError):
        Devices.model_validate(d)


@pytest.mark.parametrize('d', (
    {
        'name': 'test',
        'type': 'test',
        'memory': 65536,
        'os': {
            'variant': 'test',
            'arch': 'i686',
        },
    },
))
def test_DomainInfo_valid(d: dict) -> None:
    '''Check validation of known-good DomainInfo dicts.'''
    DomainInfo.model_validate(d)


@pytest.mark.parametrize('d', (
    dict(),
))
def test_DomainInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad DomainInfo dicts.'''
    with pytest.raises(ValidationError):
        DomainInfo.model_validate(d)
