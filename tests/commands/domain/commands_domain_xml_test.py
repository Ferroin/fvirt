# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.xml'''

from __future__ import annotations

from typing import TYPE_CHECKING

from lxml import etree

from fvirt.cli import cli

from ...shared import compare_xml_trees

if TYPE_CHECKING:
    from click.testing import CliRunner

    from fvirt.libvirt import Hypervisor


def test_command_run(cli_runner: CliRunner, test_hv: Hypervisor) -> None:
    '''Test that the command runs correctly.'''
    result = cli_runner.invoke(cli, ('-c', str(test_hv.uri), 'domain', 'xml', '1'))
    assert result.exit_code == 0
    assert len(result.output) > 0

    output_xml = etree.XML(result.output)

    with test_hv as hv:
        dom = hv.domains.get(1)
        assert dom is not None
        dom_xml = dom.config

    compare_xml_trees(dom_xml, output_xml)
