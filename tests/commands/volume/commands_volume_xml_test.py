# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.xml'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from lxml import etree

from ...shared import compare_xml_trees

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool, Volume


@pytest.mark.libvirtd
def test_command_run(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)

    result = runner(('-c', uri, 'volume', 'xml', pool.name, vol.name), 0)
    assert len(result.output) > 0

    output_xml = etree.XML(result.output)
    vol_xml = vol.config

    compare_xml_trees(vol_xml, output_xml)
