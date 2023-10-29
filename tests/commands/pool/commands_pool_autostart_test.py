# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.autostart'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager

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
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    serial: Callable[[str], _GeneratorContextManager[None]],
    worker_id: str,
) -> None:
    '''Test that running the command on multiple objects works.'''
    uri = str(live_hv.uri)
    count = 3

    with serial('live-pool'):
        pools = tuple(
            live_hv.define_storage_pool(pool_xml()) for _ in range(0, count)
        )

    assert all((not p.autostart) for p in pools)

    result = runner(('-c', uri, 'pool', 'autostart', '--enable', '--match', 'name', f'fvirt-test-{worker_id}-'), 0)
    assert len(result.output) > 0

    assert all(p.autostart for p in pools)

    with serial('live-pool'):
        for p in pools:
            p.undefine()
