# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.autostart'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool: tuple[StoragePool, Hypervisor],
) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)

    assert pool.autostart == False  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', '--enable', pool.name), 0)
    assert len(result.output) > 0

    assert pool.autostart == True  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', '--disable', pool.name), 0)
    assert len(result.output) > 0

    assert pool.autostart == False  # noqa: E712


def test_command_run_bulk(
    runner: Callable[[Sequence[str], int], Result],
    live_pool_group: tuple[tuple[StoragePool, ...], Hypervisor],
    object_name_prefix: str,
) -> None:
    '''Test that running the command on multiple objects works.'''
    pools, hv = live_pool_group
    uri = str(hv.uri)

    assert all((not p.autostart) for p in pools)

    result = runner(('-c', uri, 'pool', 'autostart', '--enable', '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    assert all(p.autostart for p in pools)
