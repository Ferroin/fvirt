# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.refresh'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: StoragePool) -> None:
    '''Test that the command runs correctly.'''
    assert len(live_pool.volumes) == 0

    uri = str(live_pool._hv.uri)
    path = Path(live_pool.target) / 'test-volume'

    path.touch(exist_ok=False)
    path.write_bytes(b'\0' * 65536)

    result = runner(('-c', uri, 'pool', 'refresh', live_pool.name), 0)
    assert len(result.output) > 0

    assert len(live_pool.volumes) == 1


@pytest.mark.xfail(reason='Test not yet implemented')
def test_command_bulk_run() -> None:
    '''Test running the command on multiple objects.'''
    assert False
