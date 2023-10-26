# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.start'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: StoragePool) -> None:
    '''Test that the command runs correctly.'''
    if live_pool.running:
        live_pool.destroy()

    assert not live_pool.running

    uri = str(live_pool._hv.uri)

    result = runner(('-c', uri, 'pool', 'start', live_pool.name), 0)
    assert len(result.output) > 0

    assert live_pool.running


@pytest.mark.xfail(reason='Test not yet implemented')
def test_command_bulk_run() -> None:
    '''Test running the command on multiple objects.'''
    assert False
