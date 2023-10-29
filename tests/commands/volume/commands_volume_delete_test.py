# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.delete'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool, Volume


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)
    name = vol.name

    result = runner(('-c', uri, 'volume', 'delete', pool.name, vol.name), 0)
    assert len(result.output) > 0

    vol1 = pool.volumes.get(name)

    assert vol1 is None


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_volume_group: tuple[tuple[Volume], StoragePool, Hypervisor],
    worker_id: str,
) -> None:
    '''Test running the command on multiple objects.'''
    vols, pool, hv = live_volume_group
    uri = str(hv.uri)

    assert len(pool.volumes) == len(vols)

    result = runner(('-c', uri, 'volume', 'delete', pool.name, '--match', 'name', f'fvirt-test-{worker_id}'), 0)
    assert len(result.output) > 0

    assert len(pool.volumes) == 0
