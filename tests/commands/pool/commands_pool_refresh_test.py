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

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool

    assert len(pool.volumes) == 0

    uri = str(hv.uri)
    path = Path(pool.target) / 'test-volume'

    path.touch(exist_ok=False)
    path.write_bytes(b'\0' * 65536)

    result = runner(('-c', uri, 'pool', 'refresh', pool.name), 0)
    assert len(result.output) > 0

    assert len(pool.volumes) == 1


@pytest.mark.xfail(reason='Test not yet implemented')
def test_command_bulk_run() -> None:
    '''Test running the command on multiple objects.'''
    assert False
