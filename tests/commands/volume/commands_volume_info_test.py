# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.info'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from fvirt.commands.volume._mixin import VolumeMixin

from ..shared import check_info_output

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool, Volume


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)

    result = runner(('-c', uri, 'volume', 'info', pool.name, vol.name), 0)
    assert len(result.output) > 0

    check_info_output(result.output, vol, f'Volume: { vol.name }', VolumeMixin)

    match = re.search(f'^  Storage Pool: { pool.name }$', result.output, re.MULTILINE)
    assert match, 'Storage pool reference not found in output.'
