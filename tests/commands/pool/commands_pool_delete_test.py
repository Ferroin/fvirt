# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.delete'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fvirt.commands._base.exitcode import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    path = Path(pool.target)

    assert path.exists()
    assert path.is_dir()

    runner(('-c', uri, 'pool', 'delete', pool.name), int(ExitCode.OPERATION_FAILED))

    assert path.exists()
    assert path.is_dir()

    pool.destroy(idempotent=True)

    runner(('-c', uri, 'pool', 'delete', pool.name), 0)

    assert not path.exists()


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool_group: tuple[tuple[StoragePool, ...], Hypervisor],
    worker_id: str,
) -> None:
    '''Test running the command on multiple objects.'''
    pools, hv = live_pool_group
    uri = str(hv.uri)

    assert all(p.running for p in pools)

    paths = tuple(
        Path(p.target) for p in pools
    )

    assert all(p.exists() for p in paths)
    assert all(p.is_dir() for p in paths)

    runner(('-c', uri, 'pool', 'delete', '--match', 'name', f'fvirt-test-{worker_id}'), int(ExitCode.OPERATION_FAILED))

    assert all(p.exists() for p in paths)
    assert all(p.is_dir() for p in paths)

    for p in pools:
        p.destroy()

    assert all((not p.running) for p in pools)

    runner(('-c', uri, 'pool', 'delete', '--match', 'name', f'fvirt-test-{worker_id}'), 0)

    assert all((not p.exists()) for p in paths)
