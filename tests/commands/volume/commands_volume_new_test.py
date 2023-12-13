# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.new'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool: tuple[StoragePool, Hypervisor],
    volume_xml: Callable[[StoragePool], str],
    tmp_path: Path,
) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    vol_xml_path = tmp_path / 'volume.xml'

    vol_xml_path.write_text(volume_xml(pool))

    result = runner(('-c', uri, 'volume', 'new', pool.name, str(vol_xml_path)), 0)

    try:
        assert len(result.output) > 0

        assert len(pool.volumes) == 1
    finally:
        for vol in pool.volumes:
            vol.undefine()


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool: tuple[StoragePool, Hypervisor],
    volume_xml: Callable[[StoragePool], str],
    tmp_path: Path,
) -> None:
    '''Test running the command on multiple objects.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    count = 3
    vol_xml_paths = [
        tmp_path / f'volume{x}.xml' for x in range(0, count)
    ]

    for p in vol_xml_paths:
        p.write_text(volume_xml(pool))

    result = runner(('-c', uri, 'volume', 'new', pool.name) + tuple(str(p) for p in vol_xml_paths), 0)

    try:
        assert len(result.output) > 0

        assert len(pool.volumes) == count
    finally:
        for vol in pool.volumes:
            vol.undefine()
