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

from lxml import etree

from fvirt.libvirt import Hypervisor, InvalidOperation, LifecycleResult, PlatformNotSupported, StoragePool
from fvirt.libvirt.volume import MATCH_ALIASES, Volume
from fvirt.util.match import MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping,
                     check_entity_access_match, check_entity_format, check_match_aliases, check_undefine)

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.libvirtd
def test_check_match_aliases(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check typing for match aliases.'''
    vol, _, _ = live_volume
    check_match_aliases(MATCH_ALIASES, vol)


@pytest.mark.libvirtd
def test_equality(live_pool: tuple[StoragePool, Hypervisor], volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test that pool equality checks work correctly.'''
    pool, _ = live_pool
    vol1 = volume_factory(pool)
    vol2 = volume_factory(pool)

    assert vol1 == vol1
    assert vol2 == vol2
    assert vol1 != vol2

    vol3 = pool.volumes.get(vol1.name)

    assert vol1 == vol3

    assert vol1 != ''


@pytest.mark.libvirtd
def test_self_wrap(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that instantiating a Volume with another Volume instance produces an equal Volume.'''
    vol, _, _ = live_volume
    assert Volume(vol) == vol


@pytest.mark.libvirtd
def test_format(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that formatting a Volume instance can be formatted.'''
    vol, _, _ = live_volume
    check_entity_format(vol)


@pytest.mark.libvirtd
def test_name(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check the name attribute.'''
    vol, _, _ = live_volume
    assert isinstance(vol.name, str)


@pytest.mark.libvirtd
def test_key(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check the key attribute.'''
    vol, _, _ = live_volume
    assert isinstance(vol.key, str)


@pytest.mark.libvirtd
def test_config_raw(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that the config_raw property works correctly.'''
    vol, _, _ = live_volume
    conf = vol.config_raw

    assert isinstance(conf, str)

    etree.fromstring(conf)

    with pytest.raises(InvalidOperation):
        vol.config_raw = conf


@pytest.mark.libvirtd
def test_config(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that the config property works correctly.'''
    vol, _, _ = live_volume
    conf = vol.config

    assert isinstance(conf, etree._ElementTree)

    with pytest.raises(InvalidOperation):
        vol.config = conf


@pytest.mark.libvirtd
def test_xslt(live_volume: tuple[Volume, StoragePool, Hypervisor], xslt_doc_factory: Callable[[str, str], str]) -> None:
    '''Check that the apply_xslt() method properly throws an InvalidOperation error.'''
    vol, _, _ = live_volume
    xslt = etree.XSLT(etree.fromstring(xslt_doc_factory('target/path', '/test')))

    with pytest.raises(InvalidOperation):
        vol.apply_xslt(xslt)


@pytest.mark.libvirtd
def test_undefine(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that undefining a volume works.'''
    vol, pool, _ = live_volume
    check_undefine(pool, 'volumes', vol)


@pytest.mark.libvirtd
def test_delete(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that deleting a volume works.'''
    vol, pool, _ = live_volume
    assert vol.valid == True  # noqa: E712

    name = vol.name

    result = vol.undefine(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert vol.valid == (not vol._mark_invalid_on_undefine)
    assert pool.volumes.get(name) is None

    result = vol.undefine(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert vol.valid == (not vol._mark_invalid_on_undefine)
    assert pool.volumes.get(name) is None

    result = vol.undefine(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert vol.valid == (not vol._mark_invalid_on_undefine)
    assert pool.volumes.get(name) is None


@pytest.mark.libvirtd
@pytest.mark.slow
def test_wipe(live_pool: tuple[StoragePool, Hypervisor], volume_factory: Callable[[StoragePool, int], Volume]) -> None:
    '''Test that wiping volumes works correctly.'''
    pool, _ = live_pool
    vol = volume_factory(pool, 65536)  # Smaller than default intentionally to speed up the test.

    try:
        path = Path(vol.path)
        size = vol.capacity
        data = b'\x00\x55\xAA\xFF' * (size // 4)

        path.write_bytes(data)
        pool.refresh()

        result = vol.wipe()

        assert result == LifecycleResult.SUCCESS
        assert vol.capacity == size

        wiped_data = path.read_bytes()

        assert wiped_data != data
    finally:
        vol.undefine()


@pytest.mark.libvirtd
def test_resize_invalid(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that resizing volumes fails correctly in invalid cases.'''
    vol, _, _ = live_volume

    with pytest.raises(ValueError, match=' is not an integer.'):
        vol.resize('')  # type: ignore

    with pytest.raises(ValueError, match='Capacity must be non-negative.'):
        vol.resize(-1)

    with pytest.raises(ValueError, match='Capacity must be non-negative.'):
        vol.resize(-1, delta=True)

    with pytest.raises(ValueError, match='Capacity must be non-negative.'):
        vol.resize(-1, shrink=True)

    with pytest.raises(ValueError, match='1024 is less than current volume size and shrink is False'):
        vol.resize(1024)


@pytest.mark.libvirtd
def test_resize_absolute(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that resizing volumes works correctly with absolute sizes.'''
    vol, _, _ = live_volume
    size = vol.capacity
    result = vol.resize(size, idempotent=False)

    assert result is LifecycleResult.NO_OPERATION
    assert vol.capacity == size

    result = vol.resize(size)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size

    result = vol.resize(size + 4096)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size + 4096


@pytest.mark.libvirtd
def test_resize_relative(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that resizing volumes works correctly with relative sizes.'''
    vol, _, _ = live_volume
    size = vol.capacity
    result = vol.resize(0, delta=True, idempotent=False)

    assert result is LifecycleResult.NO_OPERATION
    assert vol.capacity == size

    result = vol.resize(0, delta=True)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size

    result = vol.resize(4096, delta=True)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size + 4096


@pytest.mark.libvirtd
def test_resize_shrink(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that shrinking volumes works correctly with absolute sizes.'''
    vol, _, _ = live_volume
    size = vol.capacity
    result = vol.resize(size, shrink=True, idempotent=False)

    assert result is LifecycleResult.NO_OPERATION
    assert vol.capacity == size

    result = vol.resize(size, shrink=True)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size

    # We need to enlarge the volume without allocation before actually
    # testing shrinking, because some storage drivers won’t let you
    # shrink below allocated size.
    result = vol.resize(size + 4096, allocate=False)
    assert result is LifecycleResult.SUCCESS
    result = vol.resize(size, shrink=True)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size


@pytest.mark.libvirtd
def test_resize_shrink_relative(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that shrinking volumes works correctly with relative sizes.'''
    vol, _, _ = live_volume
    size = vol.capacity
    result = vol.resize(0, shrink=True, delta=True, idempotent=False)

    assert result is LifecycleResult.NO_OPERATION
    assert vol.capacity == size

    result = vol.resize(0, shrink=True, delta=True)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size

    # We need to enlarge the volume without allocation before actually
    # testing shrinking, because some storage drivers won’t let you
    # shrink below allocated size.
    result = vol.resize(4096, delta=True, allocate=False)
    assert result is LifecycleResult.SUCCESS
    result = vol.resize(4096, delta=True, shrink=True)

    assert result is LifecycleResult.SUCCESS
    assert vol.capacity == size


@pytest.mark.libvirtd
def test_volume_access_iterable(live_pool: tuple[StoragePool, Hypervisor], volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access behavior.'''
    pool, _ = live_pool
    vol = volume_factory(pool)

    try:
        check_entity_access_iterable(pool.volumes, Volume)
    finally:
        vol.undefine()


@pytest.mark.libvirtd
def test_volume_access_get(live_pool: tuple[StoragePool, Hypervisor], volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access get method.'''
    pool, _ = live_pool
    vol = volume_factory(pool)
    try:
        check_entity_access_get(pool.volumes, vol.name, Volume)
    finally:
        vol.undefine()


@pytest.mark.libvirtd
def test_volume_access_match(live_pool: tuple[StoragePool, Hypervisor], volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access match method.'''
    pool, _ = live_pool
    vol = volume_factory(pool)
    try:
        check_entity_access_match(pool.volumes, (MatchTarget(property='name'), re.compile(f'^{ vol.name }$')), Volume)
    finally:
        vol.undefine()


@pytest.mark.libvirtd
def test_volume_access_mapping(live_pool: tuple[StoragePool, Hypervisor], volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test volume entity access mappings.'''
    pool, _ = live_pool
    vol = volume_factory(pool)
    try:
        check_entity_access_mapping(pool.volumes, 'by_name', (vol.name,), str, Volume)
    finally:
        vol.undefine()


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_download(live_volume: tuple[Volume, StoragePool, Hypervisor], unique: Callable[..., Any]) -> None:
    '''Test volume download functionality.'''
    vol, _, _ = live_volume
    vol_path = Path(vol.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test'))

    vol_path.write_bytes(random.randbytes(vol.capacity))

    with target_path.open('wb') as f:
        result = vol.download(f, sparse=False)

    assert isinstance(result, int)
    assert result == vol.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
@pytest.mark.xfail(condition=sys.platform == 'win32', reason='Sparse data handling not supported on Windows', raises=PlatformNotSupported)
def test_volume_sparse_download(live_volume: tuple[Volume, StoragePool, Hypervisor], unique: Callable[..., Any]) -> None:
    '''Test volume sparse download functionality.'''
    vol, _, _ = live_volume
    vol_path = Path(vol.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test'))

    block_count = 8
    block = vol.capacity // block_count

    with vol_path.open('wb') as f:
        for k in range(0, block_count // 2):
            f.seek(block, os.SEEK_CUR)
            f.write(random.randbytes(block))

    with target_path.open('wb') as f:
        result = vol.download(f, sparse=True)

    assert isinstance(result, int)
    assert result == (block * (block_count / 2))
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload(live_volume: tuple[Volume, StoragePool, Hypervisor], unique: Callable[..., Any]) -> None:
    '''Test volume upload functionality.'''
    vol, _, _ = live_volume
    vol_path = Path(vol.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test'))

    target_path.write_bytes(random.randbytes(vol.capacity))

    with target_path.open('r+b') as f:
        result = vol.upload(f, sparse=False, resize=False)

    assert isinstance(result, int)
    assert result == vol.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload_resize(live_volume: tuple[Volume, StoragePool, Hypervisor], unique: Callable[..., Any]) -> None:
    '''Test volume upload functionality.'''
    vol, _, _ = live_volume
    vol_path = Path(vol.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test'))

    target_path.write_bytes(random.randbytes(vol.capacity * 2))

    with target_path.open('r+b') as f:
        result = vol.upload(f, sparse=False, resize=True)

    assert isinstance(result, int)
    assert result == vol.capacity
    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
@pytest.mark.xfail(condition=sys.platform == 'win32', reason='Sparse data handling not supported on Windows', raises=PlatformNotSupported)
def test_volume_sparse_upload(live_volume: tuple[Volume, StoragePool, Hypervisor], unique: Callable[..., Any]) -> None:
    '''Test volume sparse upload functionality.'''
    vol, _, _ = live_volume
    vol_path = Path(vol.path)
    target_path = vol_path.with_name(unique('text', prefix='fvirt-test'))

    block_count = 8
    block = vol.capacity // block_count

    with target_path.open('wb') as f:
        for k in range(0, block_count // 2):
            f.seek(block, os.SEEK_CUR)
            f.write(random.randbytes(block))

    with target_path.open('r+b') as f:
        result = vol.upload(f, sparse=True, resize=False)

    assert isinstance(result, int)
    assert result == (block * (block_count / 2))
    assert filecmp.cmp(vol_path, target_path, shallow=False)
