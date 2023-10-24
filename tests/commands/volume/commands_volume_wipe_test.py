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

    from fvirt.libvirt import StoragePool, Volume


@pytest.mark.libvirtd
@pytest.mark.slow
def test_volume_wipe(runner: Callable[..., Result], live_pool: StoragePool, volume_factory: Callable[[StoragePool, int], Volume]) -> None:
    '''Test that the volume wipe command works correctly.'''
    uri = str(live_pool._hv.uri)
    vol = volume_factory(live_pool, 65536)  # Smaller than default intentionally to speed up the test.

    try:
        path = Path(vol.path)
        size = vol.capacity
        data = b'\x00\x55\xAA\xFF' * (size // 4)

        path.write_bytes(data)

        runner(('-c', uri, 'volume', 'wipe', live_pool.name, vol.name), 0)

        assert vol.capacity == size

        wiped_data = path.read_bytes()

        assert wiped_data != data
    finally:
        vol.undefine()
