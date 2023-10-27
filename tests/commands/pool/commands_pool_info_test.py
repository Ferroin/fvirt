# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.info'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.pool.info import INFO_ITEMS

from ..shared import check_info_items, check_info_output

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_info_items(test_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the defined info items are valid.'''
    pool, _ = test_pool
    check_info_items(INFO_ITEMS, pool)


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)

    result = runner(('-c', uri, 'pool', 'info', pool.name), 0)
    assert len(result.output) > 0

    check_info_output(result.output, INFO_ITEMS, pool, f'Storage Pool: { pool.name }')
