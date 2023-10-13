# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.storage_pool'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Type
from uuid import UUID

import pytest

from lxml import etree

from fvirt.libvirt import EntityRunning, Hypervisor, LifecycleResult, Volume
from fvirt.libvirt.storage_pool import MATCH_ALIASES, StoragePool
from fvirt.util.match import MatchArgument, MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping,
                     check_entity_access_match, check_match_aliases, check_runnable_destroy, check_runnable_start, check_undefine)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager


def test_check_match_aliases(live_pool: StoragePool) -> None:
    '''Check typing for match aliases.'''
    check_match_aliases(MATCH_ALIASES, live_pool)


def test_name(live_pool: StoragePool) -> None:
    '''Check the name attribute.'''
    assert isinstance(live_pool.name, str)


def test_defineVolume(
        live_pool: StoragePool,
        volume_xml: Callable[[StoragePool], str],
) -> None:
    '''Test creating a volume.'''
    vol_xml = volume_xml(live_pool)
    result = live_pool.defineVolume(vol_xml)

    assert isinstance(result, Volume)


def test_numVolumes(
        live_pool: StoragePool,
        volume_factory: Callable[[StoragePool], Volume],
) -> None:
    '''Check the numVolumes attribute.'''
    assert isinstance(live_pool.numVolumes, int)
    assert live_pool.numVolumes == 0

    vol1 = volume_factory(live_pool)

    assert isinstance(vol1, Volume)
    assert live_pool.numVolumes == 1

    vol2 = volume_factory(live_pool)

    assert isinstance(vol2, Volume)
    assert live_pool.numVolumes == 2


def test_stop(live_pool: StoragePool) -> None:
    '''Check that stopping a pool works.'''
    check_runnable_destroy(live_pool)


def test_start(live_pool: StoragePool) -> None:
    '''Check that starting a pool works.'''
    check_runnable_start(live_pool)


def test_undefine(live_pool: StoragePool) -> None:
    '''Check that undefining a pool works.'''
    check_undefine(live_pool._hv, 'pools', live_pool)


def test_refresh(live_pool: StoragePool) -> None:
    '''Check that refreshing a pool works.'''
    assert live_pool.refresh() == LifecycleResult.SUCCESS


def test_build(live_hv: Hypervisor, pool_xml: Callable[[], str]) -> None:
    '''Check that building a pool works.'''
    pool = live_hv.defineStoragePool(pool_xml())

    result = pool.build()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS

    pool.undefine()


def test_delete(
        live_pool: StoragePool,
        volume_factory: Callable[[StoragePool], Volume],
) -> None:
    '''Check that deleting a pool works.'''
    assert live_pool.numVolumes == 0
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


def test_pool_access_iterable(test_hv: Hypervisor, serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Test pool entity access behavior.'''
    with serial('pool'):
        check_entity_access_iterable(test_hv.pools, StoragePool)


@pytest.mark.parametrize('k', (
    'default-pool',
    'dfe224cb-28fb-8dd0-c4b2-64eb3f0f4566',
    UUID('dfe224cb-28fb-8dd0-c4b2-64eb3f0f4566'),
))
def test_pool_access_get(test_hv: Hypervisor, k: int | str | UUID) -> None:
    '''Test pool entity access get method.'''
    check_entity_access_get(test_hv.pools, k, StoragePool)


@pytest.mark.parametrize('m', (
    (MatchTarget(property='name'), re.compile('^default-pool$')),
    (MatchTarget(property='persistent'), re.compile('^True$')),
    (MatchTarget(xpath=etree.XPath('./target/path/text()[1]')), re.compile('^/default-pool$')),
))
def test_pool_access_match(test_hv: Hypervisor, m: MatchArgument) -> None:
    '''Test pool entity access match method.'''
    check_entity_access_match(test_hv.pools, m, StoragePool)


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
    check_entity_access_mapping(test_hv.pools, p, k, c, StoragePool)
