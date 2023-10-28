# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.delete'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from fvirt.commands._base.exitcode import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    path = Path(pool.target)

    assert path.exists()
    assert path.is_dir()

    runner(('-c', uri, 'pool', 'delete', pool.name), int(ExitCode.OPERATION_FAILED))

    assert path.exists()
    assert path.is_dir()

    pool.destroy(idempotent=True)

    runner(('-c', uri, 'pool', 'delete', pool.name), 0)

    assert not path.exists()


@pytest.mark.xfail(reason='Test not yet implemented')
def test_command_bulk_run() -> None:
    '''Test running the command on multiple objects.'''
    assert False
