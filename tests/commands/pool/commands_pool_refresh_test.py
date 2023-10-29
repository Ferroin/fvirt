# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.refresh'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool

    assert len(pool.volumes) == 0

    uri = str(hv.uri)
    path = Path(pool.target) / 'test-volume'

    path.touch(exist_ok=False)
    path.write_bytes(b'\0' * 65536)

    result = runner(('-c', uri, 'pool', 'refresh', pool.name), 0)
    assert len(result.output) > 0

    assert len(pool.volumes) == 1


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool_group: tuple[tuple[StoragePool, ...], Hypervisor],
    worker_id: str,
) -> None:
    '''Test running the command on multiple objects.'''
    pools, hv = live_pool_group
    uri = str(hv.uri)

    assert all(len(p.volumes) == 0 for p in pools)

    for p in [Path(p.target) / 'test-volume' for p in pools]:
        p.touch(exist_ok=False)
        p.write_bytes(b'\0' * 65536)

    result = runner(('-c', uri, 'pool', 'refresh', '--match', 'name', f'fvirt-test-{worker_id}'), 0)
    assert len(result.output) > 0

    assert all(len(p.volumes) == 1 for p in pools)
