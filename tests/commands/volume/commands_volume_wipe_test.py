# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.wipe'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool, Volume


@pytest.mark.slow
def test_volume_wipe(
    runner: Callable[..., Result],
    live_pool: tuple[StoragePool, Hypervisor],
    volume_factory: Callable[[StoragePool, int], Volume],
) -> None:
    '''Test that the volume wipe command works correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    vol = volume_factory(pool, 65536)  # Smaller than default intentionally to speed up the test.

    try:
        path = Path(vol.path)
        size = vol.capacity
        data = b'\x00\x55\xAA\xFF' * (size // 4)

        path.write_bytes(data)

        runner(('-c', uri, 'volume', 'wipe', pool.name, vol.name), 0)

        assert vol.capacity == size

        wiped_data = path.read_bytes()

        assert wiped_data != data
    finally:
        vol.undefine()


@pytest.mark.slow
def test_command_bulk_run(
    runner: Callable[..., Result],
    live_pool: tuple[StoragePool, Hypervisor],
    volume_factory: Callable[[StoragePool, int], Volume],
) -> None:
    '''Test running the command on multiple objects.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    count = 3
    size = 65536
    volumes = tuple(
        volume_factory(pool, size) for _ in range(0, count)
    )

    try:
        data = b'\x00\x55\xAA\xFF' * (size // 4)

        for vol in volumes:
            assert vol.capacity == size

            path = Path(vol.path)

            path.write_bytes(data)

        runner(('-c', uri, 'volume', 'wipe', pool.name, '--match', 'name', 'fvirt-test-'), 0)

        for vol in volumes:
            assert vol.capacity == size

            wiped_data = path.read_bytes()

            assert wiped_data != data
    finally:
        for vol in volumes:
            vol.undefine()
