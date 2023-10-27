# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.upload'''

from __future__ import annotations

import filecmp
import os
import random
import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool, Volume


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload(
    runner: Callable[[Sequence[str], int], Result],
    live_volume: tuple[Volume, StoragePool, Hypervisor],
    unique: Callable[..., Any],
    tmp_path: Path,
) -> None:
    '''Test volume upload functionality.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)
    vol_path = Path(vol.path)
    target_path = tmp_path / unique('text', prefix='fvirt-test')

    target_path.write_bytes(random.randbytes(vol.capacity))

    runner(('-c', uri, 'volume', 'upload', pool.name, vol.name, str(target_path)), 0)

    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload_resize(
    runner: Callable[[Sequence[str], int], Result],
    live_volume: tuple[Volume, StoragePool, Hypervisor],
    unique: Callable[..., Any],
    tmp_path: Path,
) -> None:
    '''Test volume upload resize functionality.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)
    vol_path = Path(vol.path)
    target_path = tmp_path / unique('text', prefix='fvirt-test')

    target_path.write_bytes(random.randbytes(vol.capacity * 2))

    runner(('-c', uri, 'volume', 'upload', '--resize', pool.name, vol.name, str(target_path)), 0)

    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
@pytest.mark.skipif(sys.platform == 'win32', reason='Sparse data handling not supported on Windows')
def test_volume_sparse_upload(
    runner: Callable[[Sequence[str], int], Result],
    live_volume: tuple[Volume, StoragePool, Hypervisor],
    unique: Callable[..., Any],
    tmp_path: Path,
) -> None:
    '''Test volume sparse upload functionality.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)
    vol_path = Path(vol.path)
    target_path = tmp_path / unique('text', prefix='fvirt-test')

    block_count = 8
    block = vol.capacity // block_count

    with target_path.open('wb') as f:
        for k in range(0, block_count // 2):
            f.seek(block, os.SEEK_CUR)
            f.write(random.randbytes(block))

    runner(('-c', uri, 'volume', 'upload', '--sparse', pool.name, vol.name, str(target_path)), 0)

    assert filecmp.cmp(vol_path, target_path, shallow=False)
