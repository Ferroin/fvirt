# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Test fixtures for fvirt.libvirt'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from fvirt.libvirt import URI, Domain, Hypervisor, StoragePool, Volume

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from contextlib import _GeneratorContextManager


@pytest.fixture
def test_hv(test_uri: str) -> Hypervisor:
    return Hypervisor(hvuri=URI.from_string(test_uri))


@pytest.fixture
def live_hv(live_uri: str) -> Hypervisor:
    return Hypervisor(hvuri=URI.from_string(live_uri))


@pytest.fixture
def dom_xml(unique: Callable[[str], Any]) -> Callable[[], str]:
    '''Provide a factory that produces domain XML strings.'''
    def inner() -> str:
        name = unique('text')
        uuid = unique('uuid')

        return f'''
        <domain type='test'>
            <name>{ name }</name>
            <uuid>{ uuid }</uuid>
            <memory unit='MiB'>64</memory>
            <currentMemory unit='MiB'>32</currentMemory>
            <vcpu placement='static'>2</vcpu>
            <os>
                <type arch='x86_64'>hvm</type>
                <boot dev='hd' />
            </os>
            <clock offset='utc' />
            <devices>
                <disk type='file' device='disk'>
                    <source file='/guest/diskimage1'/>
                    <target dev='vda' bus='virtio'/>
                </disk>
                <interface type='network'>
                    <mac address='aa:bb:cc:dd:ee:ff'/>
                    <source network='default'/>
                    <target dev='testnet0'/>
                </interface>
                <memballoon model='virtio' />
            </devices>
        </domain>
        '''

    return inner


@pytest.fixture
def test_dom(
        test_hv: Hypervisor,
        dom_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]]
) -> Generator[Domain, None, None]:
    '''Provide a running Domain instance to operate on.

       Also ensures it's persistent.'''
    with serial('domain'):
        dom = test_hv.defineDomain(dom_xml())

    dom.start()

    yield dom

    with serial('domain'):
        if dom.valid:
            dom.destroy(idempotent=True)
            dom.undefine()


@pytest.fixture
def pool_xml(unique: Callable[[str], Any], tmp_path: Path) -> Callable[[], str]:
    '''Provide a factory function that produces storage pool XML strings.'''
    def inner() -> str:
        name = unique('text')
        uuid = unique('uuid')
        path = tmp_path / name

        return f'''
        <pool type='dir'>
            <name>{ name }</name>
            <uuid>{ uuid }</uuid>
            <source />
            <target>
                <path>{ path }</path>
            </target>
        </pool>
        '''

    return inner


@pytest.fixture
def live_pool(
        live_hv: Hypervisor,
        pool_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]],
) -> Generator[StoragePool, None, None]:
    '''Provide a running StoragePool instance to operate on.

       Also ensures it's persistent.'''
    with serial('pool'):
        pool = live_hv.defineStoragePool(pool_xml())

    pool.build()
    pool.start()

    yield pool

    with serial('pool'):
        if pool.valid:
            pool.destroy(idempotent=True)
            pool.delete()
            pool.undefine()


@pytest.fixture
def volume_xml(unique: Callable[[str], Any]) -> Callable[[StoragePool], str]:
    '''Provide a function that, given a storage pool, will produce an XML string for a Volume.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool) -> str:
        name = unique('text')
        path = Path(pool.target) / name

        return f'''
        <volume type='file'>
            <name>{ name }</name>
            <capacity units='bytes'>65536</capacity>
            <target>
                <path>{ path }</path>
                <format type='raw' />
            </target>
        </volume>
        '''

    return inner


@pytest.fixture
def volume_factory(volume_xml: Callable[[StoragePool], str]) -> Callable[[StoragePool], Volume]:
    '''Provide a function that defines volumes given a storage pool, name, and size.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool) -> Volume:
        return pool.defineVolume(volume_xml(pool))

    return inner


@pytest.fixture
def live_volume(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> Generator[Volume, None, None]:
    '''Provide a live volume to operate on.'''
    vol = volume_factory(live_pool)

    assert '_hv' in dir(vol)

    yield vol

    assert '_hv' in dir(vol)

    if vol.valid:
        vol.undefine()
