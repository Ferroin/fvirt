# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.xml'''

from __future__ import annotations

from typing import TYPE_CHECKING

from lxml import etree

from ...shared import compare_xml_trees

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor


def test_command_run(runner: Callable[[Sequence[str], int], Result], test_hv: Hypervisor) -> None:
    '''Test that the command runs correctly.'''
    result = runner(('-c', str(test_hv.uri), 'domain', 'xml', '1'), 0)
    assert len(result.output) > 0

    output_xml = etree.XML(result.output)

    with test_hv as hv:
        dom = hv.domains.get(1)
        assert dom is not None
        dom_xml = dom.config

    compare_xml_trees(dom_xml, output_xml)
