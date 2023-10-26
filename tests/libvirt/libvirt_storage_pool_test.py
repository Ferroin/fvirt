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
from fvirt.libvirt.storage_pool import MATCH_ALIASES, StoragePool
from fvirt.util.match import MatchArgument, MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping, check_entity_access_match,
                     check_entity_format, check_match_aliases, check_runnable_destroy, check_runnable_start, check_undefine, check_xslt)
from ..shared import compare_xml_trees

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager
    from pathlib import Path


@pytest.mark.libvirtd
def test_check_match_aliases(live_pool: StoragePool) -> None:
    '''Check typing for match aliases.'''
    check_match_aliases(MATCH_ALIASES, live_pool)


@pytest.mark.libvirtd
def test_equality(live_hv: Hypervisor, pool_xml: Callable[[], str]) -> None:
    '''Test that pool equality checks work correctly.'''
    pool1 = live_hv.define_storage_pool(pool_xml())
    pool2 = live_hv.define_storage_pool(pool_xml())

    assert pool1 == pool1
    assert pool2 == pool2
    assert pool1 != pool2

    pool3 = live_hv.storage_pools.get(pool1.name)

    assert pool1 == pool3

    assert pool1 != ''


@pytest.mark.libvirtd
def test_self_wrap(live_pool: StoragePool) -> None:
    '''Check that instantiating a StoragePool with another StoragePool instance produces an equal StoragePool.'''
    assert StoragePool(live_pool) == live_pool


@pytest.mark.libvirtd
def test_format(live_pool: StoragePool) -> None:
    '''Check that formatting a StoragePool instance can be formatted.'''
    check_entity_format(live_pool)


@pytest.mark.libvirtd
def test_name(live_pool: StoragePool) -> None:
    '''Check the name attribute.'''
    assert isinstance(live_pool.name, str)


@pytest.mark.xfail(reason='Not yet implemented')
def test_define() -> None:
    '''Check that defining a pool works.'''
    assert False


@pytest.mark.libvirtd
def test_config_raw(live_pool: StoragePool, tmp_path: Path) -> None:
    '''Test the config_raw property.'''
    conf = live_pool.config_raw

    assert isinstance(conf, str)

    new_conf = conf.replace(f'<path>{ live_pool.target }</path>', f'<path>{ str(tmp_path) }</path>')

    assert conf != new_conf

    live_pool.config_raw = new_conf

    e = etree.fromstring(live_pool.config_raw).find('./target/path')
    assert e is not None

    assert e.text == str(tmp_path)


@pytest.mark.libvirtd
def test_invalid_config_raw(live_pool: StoragePool, capfd: pytest.CaptureFixture) -> None:
    '''Test trying to use a bogus config with the config_raw property.'''
    conf = live_pool.config_raw

    assert isinstance(conf, str)

    bad_conf = conf.replace(f'<path>{ live_pool.target }</path>', '')

    with pytest.raises(InvalidConfig):
        live_pool.config_raw = bad_conf


@pytest.mark.libvirtd
def test_config(live_pool: StoragePool, tmp_path: Path) -> None:
    '''Test the config property.'''
    conf = live_pool.config

    assert isinstance(conf, etree._ElementTree)

    e = conf.find('/target/path')
    assert e is not None

    e.text = str(tmp_path)

    live_pool.config = conf
    live_pool.refresh()

    assert cast(etree._Element, live_pool.config.find('/target/path')).text == str(tmp_path)


@pytest.mark.libvirtd
def test_invalid_config(live_pool: StoragePool, capfd: pytest.CaptureFixture) -> None:
    '''Test trying to use a bogus config with the config property.'''
    conf = live_pool.config

    assert isinstance(conf, etree._ElementTree)

    e = conf.find('/target/path')
    assert e is not None

    e.text = ''

    with pytest.raises(InvalidConfig):
        live_pool.config = conf


@pytest.mark.libvirtd
def test_config_raw_live(live_pool: StoragePool, tmp_path: Path) -> None:
    '''Test that the config_raw_live property works as expected.'''
    conf = live_pool.config_raw
    live_conf = live_pool.config_raw_live
    target = live_pool.target

    assert isinstance(conf, str)
    assert isinstance(live_conf, str)

    new_conf = conf.replace(f'<path>{ live_pool.target }</path>', f'<path>{ str(tmp_path) }</path>')

    assert conf != new_conf

    live_pool.config_raw = new_conf
    live_pool.refresh()

    e1 = etree.fromstring(live_pool.config_raw).find('./target/path')
    assert e1 is not None

    assert e1.text == str(tmp_path)

    e2 = etree.fromstring(live_pool.config_raw_live).find('./target/path')
    assert e2 is not None

    assert e2.text == target


@pytest.mark.libvirtd
def test_config_live(live_pool: StoragePool, tmp_path: Path) -> None:
    '''Test that the config_raw_live property works as expected.'''
    conf = live_pool.config
    live_conf = live_pool.config_live

    assert isinstance(conf, etree._ElementTree)
    assert isinstance(live_conf, etree._ElementTree)

    e = conf.find('/target/path')
    assert e is not None

    e.text = str(tmp_path)

    live_pool.config = conf

    assert cast(etree._Element, live_pool.config.find('/target/path')).text == str(tmp_path)
    assert cast(etree._Element, live_pool.config_live.find('/target/path')).text != str(tmp_path)


@pytest.mark.xfail(reason='Not yet implemented')
def test_create() -> None:
    '''Check that creating a domain works.'''
    assert False


@pytest.mark.libvirtd
def test_undefine(live_pool: StoragePool) -> None:
    '''Check that undefining a pool works.'''
    check_undefine(live_pool._hv, 'storage_pools', live_pool)


@pytest.mark.libvirtd
def test_define_volume(
        live_pool: StoragePool,
        volume_xml: Callable[[StoragePool], str],
) -> None:
    '''Test creating a volume.'''
    vol_xml = volume_xml(live_pool)
    result = live_pool.define_volume(vol_xml)

    assert isinstance(result, Volume)


@pytest.mark.libvirtd
def test_num_volumes(
        live_pool: StoragePool,
        volume_factory: Callable[[StoragePool], Volume],
) -> None:
    '''Check the num_volumes attribute.'''
    assert isinstance(live_pool.num_volumes, int)
    assert live_pool.num_volumes == 0

    vol1 = volume_factory(live_pool)

    assert isinstance(vol1, Volume)
    assert live_pool.num_volumes == 1

    vol2 = volume_factory(live_pool)

    assert isinstance(vol2, Volume)
    assert live_pool.num_volumes == 2


@pytest.mark.libvirtd
def test_stop(live_pool: StoragePool) -> None:
    '''Check that stopping a pool works.'''
    check_runnable_destroy(live_pool)


@pytest.mark.libvirtd
def test_start(live_pool: StoragePool) -> None:
    '''Check that starting a pool works.'''
    check_runnable_start(live_pool)


@pytest.mark.libvirtd
def test_refresh(live_pool: StoragePool) -> None:
    '''Check that refreshing a pool works.'''
    assert live_pool.refresh() == LifecycleResult.SUCCESS


@pytest.mark.libvirtd
def test_build(live_hv: Hypervisor, pool_xml: Callable[[], str]) -> None:
    '''Check that building a pool works.'''
    pool = live_hv.define_storage_pool(pool_xml())

    result = pool.build()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS

    pool.undefine()


@pytest.mark.libvirtd
def test_delete(
        live_pool: StoragePool,
        volume_factory: Callable[[StoragePool], Volume],
) -> None:
    '''Check that deleting a pool works.'''
    assert live_pool.num_volumes == 0
    assert live_pool.running == True  # noqa: E712

    with pytest.raises(EntityRunning):
        result = live_pool.delete(idempotent=False)

    live_pool.destroy()

    result = live_pool.delete(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS

    result = live_pool.delete(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.FAILURE


@pytest.mark.xfail(reason='Not working due to apparent libvirt bug')
def test_xslt(live_pool: StoragePool) -> None:
    '''Check that applying an XSLT document to a pool works correctly.'''
    check_xslt(live_pool, '/target/path', '/test', 'target')


def test_pool_access_iterable(test_hv: Hypervisor, serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Test pool entity access behavior.'''
    with serial('pool'):
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
def test_entities(test_pool: StoragePool, t: str) -> None:
    '''Check that entity access attributes exist.'''
    assert hasattr(test_pool, t)

    assert isinstance(getattr(test_pool, t), EntityAccess)
