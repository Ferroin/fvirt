# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.volume'''

from __future__ import annotations

import filecmp
import os
import random
import re
import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from fvirt.libvirt import LifecycleResult, PlatformNotSupported, StoragePool
from fvirt.libvirt.volume import MATCH_ALIASES, Volume
from fvirt.util.match import MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping,
                     check_entity_access_match, check_entity_format, check_match_aliases, check_undefine)

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.libvirtd
def test_check_match_aliases(live_volume: Volume) -> None:
    '''Check typing for match aliases.'''
    check_match_aliases(MATCH_ALIASES, live_volume)


@pytest.mark.libvirtd
def test_format(live_volume: Volume) -> None:
    '''Check that formatting a Volume instance can be formatted.'''
    check_entity_format(live_volume)


@pytest.mark.libvirtd
def test_name(live_volume: Volume) -> None:
    '''Check the name attribute.'''
    assert isinstance(live_volume.name, str)


@pytest.mark.libvirtd
def test_key(live_volume: Volume) -> None:
    '''Check the key attribute.'''
    assert isinstance(live_volume.key, str)


@pytest.mark.libvirtd
def test_undefine(live_volume: Volume) -> None:
    '''Check that undefining a volume works.'''
    assert isinstance(live_volume._parent, StoragePool)
    check_undefine(live_volume._parent, 'volumes', live_volume)


@pytest.mark.libvirtd
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


@pytest.mark.libvirtd
@pytest.mark.xfail(reason='Not yet implemented.')
def test_wipe() -> None:
    '''Test that wiping volumes works correctly.'''
    assert False


@pytest.mark.libvirtd
@pytest.mark.xfail(reason='Not yet implemented.')
def test_reset() -> None:
    '''Test that resizing volumes works correctly.'''
    assert False


@pytest.mark.libvirtd
def test_volume_access_iterable(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access behavior.'''
    vol = volume_factory(live_pool)
    check_entity_access_iterable(live_pool.volumes, Volume)
    vol.undefine()


@pytest.mark.libvirtd
def test_volume_access_get(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access get method.'''
    vol = volume_factory(live_pool)
    check_entity_access_get(live_pool.volumes, vol.name, Volume)
    vol.undefine()


@pytest.mark.libvirtd
def test_volume_access_match(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access match method.'''
    vol = volume_factory(live_pool)
    check_entity_access_match(live_pool.volumes, (MatchTarget(property='name'), re.compile(f'^{ vol.name }$')), Volume)
    vol.undefine()


@pytest.mark.libvirtd
def test_volume_access_mapping(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access mappings.'''
    vol = volume_factory(live_pool)
    check_entity_access_mapping(live_pool.volumes, 'by_name', (vol.name,), str, Volume)
    vol.undefine()


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_download(live_volume: Volume, unique: Callable[..., Any]) -> None:
    '''Test volume download functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test-'))

    vol_path.write_bytes(random.randbytes(live_volume.capacity))

    with target_path.open('wb') as f:
        result = live_volume.download(f, sparse=False)

    assert isinstance(result, int)
    assert result == live_volume.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
@pytest.mark.xfail(condition=sys.platform == 'win32', reason='Sparse data handling not supported on Windows', raises=PlatformNotSupported)
def test_volume_sparse_download(live_volume: Volume, unique: Callable[..., Any]) -> None:
    '''Test volume sparse download functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test-'))

    block_count = 8
    block = live_volume.capacity // block_count

    with vol_path.open('wb') as f:
        for k in range(0, block_count // 2):
            f.seek(block, os.SEEK_CUR)
            f.write(random.randbytes(block))

    with target_path.open('wb') as f:
        result = live_volume.download(f, sparse=True)

    assert isinstance(result, int)
    assert result == (block * (block_count / 2))
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload(live_volume: Volume, unique: Callable[..., Any]) -> None:
    '''Test volume upload functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test-'))

    target_path.write_bytes(random.randbytes(live_volume.capacity))

    with target_path.open('r+b') as f:
        result = live_volume.upload(f, sparse=False, resize=False)

    assert isinstance(result, int)
    assert result == live_volume.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload_resize(live_volume: Volume, unique: Callable[..., Any]) -> None:
    '''Test volume upload functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test-'))

    target_path.write_bytes(random.randbytes(live_volume.capacity * 2))

    with target_path.open('r+b') as f:
        result = live_volume.upload(f, sparse=False, resize=True)

    assert isinstance(result, int)
    assert result == live_volume.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
@pytest.mark.xfail(condition=sys.platform == 'win32', reason='Sparse data handling not supported on Windows', raises=PlatformNotSupported)
def test_volume_sparse_upload(live_volume: Volume, unique: Callable[..., Any]) -> None:
    '''Test volume sparse upload functionality.'''
    vol_path = Path(live_volume.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test-'))

    block_count = 8
    block = live_volume.capacity // block_count

    with target_path.open('wb') as f:
        for k in range(0, block_count // 2):
            f.seek(block, os.SEEK_CUR)
            f.write(random.randbytes(block))

    with target_path.open('r+b') as f:
        result = live_volume.upload(f, sparse=True, resize=False)

    assert isinstance(result, int)
    assert result == (block * (block_count / 2))
    assert filecmp.cmp(vol_path, target_path, shallow=False)
