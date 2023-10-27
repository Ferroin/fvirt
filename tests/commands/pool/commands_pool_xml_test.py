# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.xml'''

from __future__ import annotations

from typing import TYPE_CHECKING

from lxml import etree

from ...shared import compare_xml_trees

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(runner: Callable[[Sequence[str], int], Result], live_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)

    result = runner(('-c', uri, 'pool', 'xml', pool.name), 0)
    assert len(result.output) > 0

    output_xml = etree.XML(result.output)
    pool_xml = pool.config

    compare_xml_trees(pool_xml, output_xml)
