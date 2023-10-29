# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.start'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool

    if pool.running:
        pool.destroy()

    assert not pool.running

    uri = str(hv.uri)

    result = runner(('-c', uri, 'pool', 'start', pool.name), 0)
    assert len(result.output) > 0

    assert pool.running


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool_group: tuple[tuple[StoragePool, ...], Hypervisor],
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    pools, hv = live_pool_group
    uri = str(hv.uri)

    for p in pools:
        p.destroy(idempotent=True)

    assert all((not p.running) for p in pools)

    result = runner(('-c', uri, 'pool', 'start', '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    assert all(p.running for p in pools)
