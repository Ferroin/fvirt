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

    from fvirt.libvirt import Volume


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload(tmp_path: Path, runner: Callable[[Sequence[str], int], Result], live_volume: Volume, unique: Callable[..., Any]) -> None:
    '''Test volume upload functionality.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    vol_path = Path(live_volume.path)
    target_path = tmp_path / unique('text', prefix='fvirt-test')

    assert pool is not None

    target_path.write_bytes(random.randbytes(live_volume.capacity))

    runner(('-c', uri, 'volume', 'upload', pool.name, live_volume.name, str(target_path)), 0)

    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
def test_volume_upload_resize(
    tmp_path: Path,
    runner: Callable[[Sequence[str], int], Result],
    live_volume: Volume,
    unique: Callable[..., Any]
) -> None:
    '''Test volume upload resize functionality.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    vol_path = Path(live_volume.path)
    target_path = tmp_path / unique('text', prefix='fvirt-test')

    assert pool is not None

    target_path.write_bytes(random.randbytes(live_volume.capacity * 2))

    runner(('-c', uri, 'volume', 'upload', '--resize', pool.name, live_volume.name, str(target_path)), 0)

    assert filecmp.cmp(vol_path, target_path, shallow=False)


@pytest.mark.slow
@pytest.mark.libvirtd
@pytest.mark.xfail(condition=sys.platform == 'win32', reason='Sparse data handling not supported on Windows')
def test_volume_sparse_upload(
    tmp_path: Path,
    runner: Callable[[Sequence[str], int], Result],
    live_volume: Volume,
    unique: Callable[..., Any],
) -> None:
    '''Test volume sparse upload functionality.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    vol_path = Path(live_volume.path)
    target_path = tmp_path / unique('text', prefix='fvirt-test')

    assert pool is not None

    block_count = 8
    block = live_volume.capacity // block_count

    with target_path.open('wb') as f:
        for k in range(0, block_count // 2):
            f.seek(block, os.SEEK_CUR)
            f.write(random.randbytes(block))

    runner(('-c', uri, 'volume', 'upload', '--sparse', pool.name, live_volume.name, str(target_path)), 0)

    assert filecmp.cmp(vol_path, target_path, shallow=False)
