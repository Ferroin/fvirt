# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.volume'''

from __future__ import annotations

import filecmp
import math
import os
import random
import re

from pathlib import Path
from typing import TYPE_CHECKING, Any

from fvirt.libvirt import LifecycleResult, StoragePool
from fvirt.libvirt.volume import MATCH_ALIASES, Volume
from fvirt.util.match import MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping,
                     check_entity_access_match, check_match_aliases, check_undefine)

if TYPE_CHECKING:
    from collections.abc import Callable


def test_check_match_aliases(live_volume: Volume) -> None:
    '''Check typing for match aliases.'''
    check_match_aliases(MATCH_ALIASES, live_volume)


def test_name(live_volume: Volume) -> None:
    '''Check the name attribute.'''
    assert isinstance(live_volume.name, str)


def test_key(live_volume: Volume) -> None:
    '''Check the key attribute.'''
    assert isinstance(live_volume.key, str)


def test_undefine(live_volume: Volume) -> None:
    '''Check that undefining a volume works.'''
    assert isinstance(live_volume._parent, StoragePool)
    check_undefine(live_volume._parent, 'volumes', live_volume)


def test_delete(live_volume: Volume) -> None:
    '''Check that deleting a volume works.'''
    assert live_volume.valid == True  # noqa: E712
    assert isinstance(live_volume._parent, StoragePool)

    pool = live_volume._parent
    name = live_volume.name

    result = live_volume.undefine(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert live_volume.valid == (not live_volume._mark_invalid_on_undefine)
    assert pool.volumes.get(name) is None

    result = live_volume.undefine(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert live_volume.valid == (not live_volume._mark_invalid_on_undefine)
    assert pool.volumes.get(name) is None

    result = live_volume.undefine(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert live_volume.valid == (not live_volume._mark_invalid_on_undefine)
    assert pool.volumes.get(name) is None


def test_volume_access_iterable(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access behavior.'''
    vol = volume_factory(live_pool)
    check_entity_access_iterable(live_pool.volumes, Volume)
    vol.undefine()


def test_volume_access_get(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access get method.'''
    vol = volume_factory(live_pool)
    check_entity_access_get(live_pool.volumes, vol.name, Volume)
    vol.undefine()


def test_volume_access_match(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access match method.'''
    vol = volume_factory(live_pool)
    check_entity_access_match(live_pool.volumes, (MatchTarget(property='name'), re.compile(f'^{ vol.name }$')), Volume)
    vol.undefine()


def test_volume_access_mapping(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access mappings.'''
    vol = volume_factory(live_pool)
    check_entity_access_mapping(live_pool.volumes, 'by_name', (vol.name,), str, Volume)
    vol.undefine()


def test_volume_download(live_volume: Volume, unique: Callable[[str], Any]) -> None:
    '''Test volume download functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text'))

    vol_path.write_bytes(random.randbytes(live_volume.capacity))

    with target_path.open('wb') as f:
        result = live_volume.download(f, sparse=False, bufsz=4096)

    assert isinstance(result, int)
    assert result == live_volume.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


def test_volume_sparse_download(live_volume: Volume, unique: Callable[[str], Any]) -> None:
    '''Test volume sparse download functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text'))

    block = math.floor(live_volume.capacity / 4)

    with vol_path.open('wb') as f:
        f.seek(block, os.SEEK_CUR)
        f.write(random.randbytes(block))
        f.seek(block, os.SEEK_CUR)
        f.write(random.randbytes(block))

    with target_path.open('wb') as f:
        result = live_volume.download(f, sparse=True, bufsz=4096)

    assert isinstance(result, int)
    assert result == (block * 2)
    assert filecmp.cmp(vol_path, target_path, shallow=False)
