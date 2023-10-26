# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.undefine'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: StoragePool) -> None:
    '''Test that the command runs correctly.'''
    assert live_pool.valid

    live_pool.destroy()

    assert not live_pool.running

    hv = live_pool._hv
    uri = str(hv.uri)
    name = live_pool.name

    result = runner(('-c', uri, 'pool', 'undefine', name), 0)
    assert len(result.output) > 0

    pool = hv.storage_pools.get(name)

    assert pool is None


@pytest.mark.xfail(reason='Test not yet implemented')
def test_command_bulk_run() -> None:
    '''Test running the command on multiple objects.'''
    assert False
