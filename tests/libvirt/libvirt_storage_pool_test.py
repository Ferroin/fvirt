# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.storage_pool'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Type, cast
from uuid import UUID

import pytest

from lxml import etree

from fvirt.libvirt import EntityRunning, Hypervisor, InvalidConfig, LifecycleResult, Volume
from fvirt.libvirt.entity_access import EntityAccess
from fvirt.libvirt.storage_pool import MATCH_ALIASES, POOL_TYPE_INFO, StoragePool, StoragePoolState
from fvirt.util.match import MatchArgument, MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping, check_entity_access_match,
                     check_entity_format, check_match_aliases, check_runnable_destroy, check_runnable_start, check_undefine, check_xslt)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager
    from pathlib import Path


def test_check_match_aliases(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check typing for match aliases.'''
    pool, _ = live_pool
    check_match_aliases(MATCH_ALIASES, pool)


def test_pool_type_info() -> None:
    '''Check typing for POOL_TYPE_INFO.'''
    assert isinstance(POOL_TYPE_INFO, dict)

    for k, v in POOL_TYPE_INFO.items():
        assert isinstance(k, str)
        assert isinstance(v, dict)

        assert 'type' in v
        assert 'name' in v
        assert 'pool' in v
        assert 'volume' in v

        assert k == v['type']

        assert isinstance(v['name'], str)

        assert isinstance(v['pool'], dict)

        assert 'formats' in v['pool']
        assert 'target' in v['pool']

        for k2, v2 in v['pool'].items():
            assert isinstance(k2, str)
            assert isinstance(v2, dict)

            match k2:
                case 'formats':
                    for k3, v3 in v2.items():
                        assert isinstance(k3, str)
                        assert isinstance(v3, str)
                case _:
                    for k3, v3 in v2.items():
                        assert isinstance(k3, str)
                        assert isinstance(v3, bool)

        assert isinstance(v['volume'], dict)

        assert 'formats' in v['volume']

        for k2, v2 in v['volume'].items():
            assert isinstance(k2, str)
            assert isinstance(v2, dict)

            match k2:
                case 'formats':
                    for k3, v3 in v2.items():
                        assert isinstance(k3, str)
                        assert isinstance(v3, str)
                case _:
                    for k3, v3 in v2.items():
                        assert isinstance(k3, str)
                        assert isinstance(v3, bool)


def test_equality(
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    serial: Callable[[str], _GeneratorContextManager[None]]
) -> None:
    '''Test that pool equality checks work correctly.'''
    with serial('live-pool'):
        pool1 = live_hv.define_storage_pool(pool_xml())
        pool2 = live_hv.define_storage_pool(pool_xml())

    assert pool1 == pool1
    assert pool2 == pool2
    assert pool1 != pool2

    pool3 = live_hv.storage_pools.get(pool1.name)

    assert pool1 == pool3

    assert pool1 != ''


def test_self_wrap(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that instantiating a StoragePool with another StoragePool instance produces an equal StoragePool.'''
    pool, _ = live_pool
    assert StoragePool(pool) == pool


def test_format(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that formatting a StoragePool instance can be formatted.'''
    pool, _ = live_pool
    check_entity_format(pool)


def test_name(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check the name attribute.'''
    pool, _ = live_pool
    assert isinstance(pool.name, str)


def test_domain_state() -> None:
    '''Check the StoragePoolState enumerable.'''
    for s in StoragePoolState:
        assert isinstance(s.value, int)

    assert len({s.value for s in StoragePoolState}) == len(StoragePoolState), 'duplicate values in StoragePoolState'
    assert len({str(s) for s in StoragePoolState}) == len(StoragePoolState), 'duplicate string representations in StoragePoolState'


def test_state(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check the state attribute.'''
    pool, _ = live_pool
    assert isinstance(pool.state, StoragePoolState)
    assert pool.state == StoragePoolState.RUNNING
    assert pool.destroy() == LifecycleResult.SUCCESS
    assert pool.state != StoragePoolState.RUNNING


def test_define(live_hv: Hypervisor, pool_xml: Callable[[], str], serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Check that defining a pool works.'''
    with serial('live-pool'):
        pool = live_hv.define_storage_pool(pool_xml())

    assert isinstance(pool, StoragePool)
    assert not pool.running


def test_config_raw(live_pool: tuple[StoragePool, Hypervisor], tmp_path: Path) -> None:
    '''Test the config_raw property.'''
    pool, _ = live_pool
    conf = pool.config_raw

    assert isinstance(conf, str)

    new_conf = conf.replace(f'<path>{ pool.target }</path>', f'<path>{ str(tmp_path) }</path>')

    assert conf != new_conf

    pool.config_raw = new_conf

    e = etree.fromstring(pool.config_raw).find('./target/path')
    assert e is not None

    assert e.text == str(tmp_path)


def test_invalid_config_raw(live_pool: tuple[StoragePool, Hypervisor], capfd: pytest.CaptureFixture) -> None:
    '''Test trying to use a bogus config with the config_raw property.'''
    pool, _ = live_pool
    conf = pool.config_raw

    assert isinstance(conf, str)

    bad_conf = conf.replace(f'<path>{ pool.target }</path>', '')

    with pytest.raises(InvalidConfig):
        pool.config_raw = bad_conf


def test_config(live_pool: tuple[StoragePool, Hypervisor], tmp_path: Path) -> None:
    '''Test the config property.'''
    pool, _ = live_pool
    conf = pool.config

    assert isinstance(conf, etree._ElementTree)

    e = conf.find('/target/path')
    assert e is not None

    e.text = str(tmp_path)

    pool.config = conf

    assert cast(etree._Element, pool.config.find('/target/path')).text == str(tmp_path)


def test_invalid_config(live_pool: tuple[StoragePool, Hypervisor], capfd: pytest.CaptureFixture) -> None:
    '''Test trying to use a bogus config with the config property.'''
    pool, _ = live_pool
    conf = pool.config

    assert isinstance(conf, etree._ElementTree)

    e = conf.find('/target/path')
    assert e is not None

    e.text = ''

    with pytest.raises(InvalidConfig):
        pool.config = conf


def test_config_raw_live(live_pool: tuple[StoragePool, Hypervisor], tmp_path: Path) -> None:
    '''Test that the config_raw_live property works as expected.'''
    pool, _ = live_pool
    conf = pool.config_raw
    live_conf = pool.config_raw_live
    target = pool.target

    assert isinstance(conf, str)
    assert isinstance(live_conf, str)

    new_conf = conf.replace(f'<path>{ pool.target }</path>', f'<path>{ str(tmp_path) }</path>')

    assert conf != new_conf

    pool.config_raw = new_conf
    pool.refresh()

    e1 = etree.fromstring(pool.config_raw).find('./target/path')
    assert e1 is not None

    assert e1.text == str(tmp_path)

    e2 = etree.fromstring(pool.config_raw_live).find('./target/path')
    assert e2 is not None

    assert e2.text == target


def test_config_live(live_pool: tuple[StoragePool, Hypervisor], tmp_path: Path) -> None:
    '''Test that the config_raw_live property works as expected.'''
    pool, _ = live_pool
    conf = pool.config
    live_conf = pool.config_live

    assert isinstance(conf, etree._ElementTree)
    assert isinstance(live_conf, etree._ElementTree)

    e = conf.find('/target/path')
    assert e is not None

    e.text = str(tmp_path)

    pool.config = conf

    assert cast(etree._Element, pool.config.find('/target/path')).text == str(tmp_path)
    assert cast(etree._Element, pool.config_live.find('/target/path')).text != str(tmp_path)


def test_create(live_hv: Hypervisor, pool_xml: Callable[[], str], serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Check that creating a pool works.'''
    with serial('live-pool'):
        pool = live_hv.create_storage_pool(pool_xml())

    assert isinstance(pool, StoragePool)
    assert pool.running


def test_undefine(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that undefining a pool works.'''
    pool, _ = live_pool
    check_undefine(pool._hv, 'storage_pools', pool)


def test_define_volume(
        live_pool: tuple[StoragePool, Hypervisor],
        volume_xml: Callable[[StoragePool], str],
) -> None:
    '''Test creating a volume.'''
    pool, _ = live_pool
    vol_xml = volume_xml(pool)
    result = pool.define_volume(vol_xml)

    assert isinstance(result, Volume)


def test_num_volumes(
        live_pool: tuple[StoragePool, Hypervisor],
        volume_factory: Callable[[StoragePool], Volume],
) -> None:
    '''Check the num_volumes attribute.'''
    pool, _ = live_pool
    assert isinstance(pool.num_volumes, int)
    assert pool.num_volumes == 0

    vol1 = volume_factory(pool)

    assert isinstance(vol1, Volume)
    assert pool.num_volumes == 1

    vol2 = volume_factory(pool)

    assert isinstance(vol2, Volume)
    assert pool.num_volumes == 2


def test_stop(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that stopping a pool works.'''
    pool, _ = live_pool
    check_runnable_destroy(pool)


def test_start(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that starting a pool works.'''
    pool, _ = live_pool
    check_runnable_start(pool)


def test_refresh(live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that refreshing a pool works.'''
    pool, _ = live_pool
    assert pool.refresh() == LifecycleResult.SUCCESS


def test_build(live_hv: Hypervisor, pool_xml: Callable[[], str], serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Check that building a pool works.'''
    # TODO: Needs a better test case that actually confirms the pool was built.
    with serial('live-pool'):
        pool = live_hv.define_storage_pool(pool_xml())

    result = pool.build()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS

    with serial('live-pool'):
        pool.undefine()


def test_delete(
        live_pool: tuple[StoragePool, Hypervisor],
        volume_factory: Callable[[StoragePool], Volume],
) -> None:
    '''Check that deleting a pool works.'''
    pool, _ = live_pool
    assert pool.num_volumes == 0
    assert pool.running == True  # noqa: E712

    with pytest.raises(EntityRunning):
        result = pool.delete(idempotent=False)

    pool.destroy()

    result = pool.delete(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS

    result = pool.delete(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.FAILURE


def test_xslt(live_pool: tuple[StoragePool, Hypervisor], xslt_doc_factory: Callable[[str, str], str], tmp_path: Path) -> None:
    '''Check that applying an XSLT document to a pool works correctly.'''
    pool, _ = live_pool
    check_xslt(pool, 'target/path', str(tmp_path), xslt_doc_factory)


def test_pool_access_iterable(test_hv: Hypervisor, serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Test pool entity access behavior.'''
    with serial('test-pool'):
        check_entity_access_iterable(test_hv.storage_pools, StoragePool)


@pytest.mark.parametrize('k', (
    'default-pool',
    'dfe224cb-28fb-8dd0-c4b2-64eb3f0f4566',
    UUID('dfe224cb-28fb-8dd0-c4b2-64eb3f0f4566'),
))
def test_pool_access_get(test_hv: Hypervisor, k: int | str | UUID) -> None:
    '''Test pool entity access get method.'''
    check_entity_access_get(test_hv.storage_pools, k, StoragePool)


@pytest.mark.parametrize('m', (
    (MatchTarget(property='name'), re.compile('^default-pool$')),
    (MatchTarget(property='persistent'), re.compile('^True$')),
    (MatchTarget(xpath=etree.XPath('./target/path/text()[1]')), re.compile('^/default-pool$')),
))
def test_pool_access_match(test_hv: Hypervisor, m: MatchArgument) -> None:
    '''Test pool entity access match method.'''
    check_entity_access_match(test_hv.storage_pools, m, StoragePool)


@pytest.mark.parametrize('p, k, c', (
    (
        'by_name',
        (
            'default-pool',
        ),
        str
    ),
    (
        'by_uuid',
        (
            'dfe224cb-28fb-8dd0-c4b2-64eb3f0f4566',
            UUID('dfe224cb-28fb-8dd0-c4b2-64eb3f0f4566'),
        ),
        UUID,
    ),
))
def test_pool_access_mapping(test_hv: Hypervisor, p: str, k: Sequence[Any], c: Type[object]) -> None:
    '''Test pool entity access mappings.'''
    check_entity_access_mapping(test_hv.storage_pools, p, k, c, StoragePool)


@pytest.mark.parametrize('t', (
    'volumes',
))
def test_entities(test_pool: tuple[StoragePool, Hypervisor], t: str) -> None:
    '''Check that entity access attributes exist.'''
    pool, _ = test_pool

    assert hasattr(pool, t)

    assert isinstance(getattr(pool, t), EntityAccess)


@pytest.mark.parametrize('data', (
    {
        'pool_type': 'dir',
        'name': 'pool',
        'target_path': '/nonexistent',
    },
    {
        'pool_type': 'fs',
        'name': 'pool',
        'pool_format': 'auto',
        'target_path': '/nonexistent',
        'devices': '/dev/hda',
    },
    {
        'pool_type': 'netfs',
        'name': 'pool',
        'pool_format': 'nfs',
        'target_path': '/nonexistent',
        'hosts': 'nfs.example.com',
        'source_path': '/pool',
        'protocol': 4,
    },
    {
        'pool_type': 'logical',
        'name': 'pool',
        'target_path': '/dev/HostVG',
        'devices': [
            '/dev/hda1',
            '/dev/hdb1',
            '/dev/hdc1',
        ],
    },
    {
        'pool_type': 'disk',
        'name': 'pool',
        'pool_format': 'gpt',
        'target_path': '/dev',
        'devices': [
            '/dev/hda',
        ],
    },
    {
        'pool_type': 'iscsi',
        'name': 'pool',
        'target_path': '/dev/disk/by-path',
        'hosts': [
            'iscsi.example.com',
        ],
        'devices': [
            'iqn.2013-06.com.example:iscsi-pool',
        ],
    },
    {
        'pool_type': 'iscsi-direct',
        'name': 'pool',
        'hosts': 'iscsi.example.com',
        'devices': 'iqn.2013-06.com.example:iscsi-pool',
        'initiator': 'iqn.2013-06.com.example:iscsi-initiator',
    },
    {
        'pool_type': 'scsi',
        'name': 'pool',
        'target_path': '/dev/disk/by-path',
        'adapter': 'host0',
    },
    {
        'pool_type': 'rbd',
        'name': 'pool',
        'source_name': 'pool',
        'hosts': [
            'mon1.example.com',
            'mon2.example.com',
            'mon3.example.com',
        ],
    },
    {
        'pool_type': 'gluster',
        'name': 'pool',
        'source_name': 'pool',
        'hosts': 'gluster.example.com',
        'source_path': '/pool',
    },
    {
        'pool_type': 'zfs',
        'name': 'pool',
        'target_path': '/nonexistent',
        'source_name': 'pool',
    },
    {
        'pool_type': 'vstorage',
        'name': 'pool',
        'target_path': '/nonexistent',
        'source_name': 'pool',
    },
))
def test_new_config(data: Any, virt_xml_validate: Callable[[str], None]) -> None:
    '''Test the new_config class method.'''
    doc = StoragePool.new_config(**data)

    assert isinstance(doc, str)

    virt_xml_validate(doc)
