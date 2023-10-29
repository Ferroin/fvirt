# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.undefine'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    assert pool.valid

    pool.destroy()

    assert not pool.running

    uri = str(hv.uri)
    name = pool.name

    result = runner(('-c', uri, 'pool', 'undefine', name), 0)
    assert len(result.output) > 0

    pool1 = hv.storage_pools.get(name)

    assert pool1 is None


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool_group: tuple[tuple[StoragePool, ...], Hypervisor],
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    pools, hv = live_pool_group
    uri = str(hv.uri)

    assert all(p.valid for p in pools)

    for p in pools:
        p.destroy()

    assert all((not p.running) for p in pools)

    result = runner(('-c', uri, 'pool', 'undefine', '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    assert all(p not in hv.storage_pools for p in pools)
