# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.build'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager

    from click.testing import Result

    from fvirt.libvirt import Hypervisor


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    serial: Callable[[str], _GeneratorContextManager[None]],
) -> None:
    '''Test that the command runs correctly.'''
    # TODO: Needs a better test case that actually confirms the pool was built.
    with serial('live-pool'):
        pool = live_hv.define_storage_pool(pool_xml())

    result = runner(('-c', str(live_hv.uri), 'pool', 'build', pool.name), 0)
    assert len(result.output) > 0

    with serial('live-pool'):
        pool.undefine()


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    serial: Callable[[str], _GeneratorContextManager[None]],
    worker_id: str,
) -> None:
    '''Test running the command on multiple objects.'''
    count = 3

    with serial('live-pool'):
        pools = tuple(live_hv.define_storage_pool(pool_xml()) for _ in range(0, count))

    result = runner(('-c', str(live_hv.uri), 'pool', 'build', '--match', 'name', f'^fvirt-test-{worker_id}'), 0)
    assert len(result.output) > 0

    with serial('live-pool'):
        for pool in pools:
            pool.undefine()
