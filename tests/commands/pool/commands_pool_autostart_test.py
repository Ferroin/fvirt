# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.autostart'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import StoragePool


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool: StoragePool,
) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_pool._hv.uri)

    assert live_pool.autostart == False  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', live_pool.name, 'yes'), 0)
    assert len(result.output) > 0

    assert live_pool.autostart == True  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', live_pool.name, 'no'), 0)
    assert len(result.output) > 0

    assert live_pool.autostart == False  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', live_pool.name, '1'), 0)
    assert len(result.output) > 0

    assert live_pool.autostart == True  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', live_pool.name, '0'), 0)
    assert len(result.output) > 0

    assert live_pool.autostart == False  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', live_pool.name, 'true'), 0)
    assert len(result.output) > 0

    assert live_pool.autostart == True  # noqa: E712

    result = runner(('-c', uri, 'pool', 'autostart', live_pool.name, 'false'), 0)
    assert len(result.output) > 0

    assert live_pool.autostart == False  # noqa: E712


@pytest.mark.xfail(reason='Not yet implemented')
def test_command_run_bulk() -> None:
    '''Test that running the command on multiple objects works.'''
    assert False
