# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.info'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING

import pytest

from fvirt.commands.volume.info import INFO_ITEMS

from ..shared import check_info_items, check_info_output

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import StoragePool, Volume


@pytest.mark.libvirtd
def test_info_items(live_volume: Volume) -> None:
    '''Test that the defined info items are valid.'''
    check_info_items(INFO_ITEMS, live_volume)


@pytest.mark.libvirtd
def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_pool._hv.uri)
    vol = volume_factory(live_pool)

    try:
        result = runner(('-c', uri, 'volume', 'info', live_pool.name, vol.name), 0)
        assert len(result.output) > 0

        check_info_output(result.output, INFO_ITEMS, vol, f'Volume: { vol.name }')

        match = re.search(f'^  Storage Pool: { live_pool.name }$', result.output, re.MULTILINE)
        assert match, 'Storage pool reference not found in output.'
    finally:
        vol.undefine()
