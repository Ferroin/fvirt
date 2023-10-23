# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.xml'''

from __future__ import annotations

from typing import TYPE_CHECKING

from lxml import etree

from fvirt.cli import cli

from ...shared import compare_xml_trees

if TYPE_CHECKING:
    from click.testing import CliRunner

    from fvirt.libvirt import StoragePool


def test_command_run(cli_runner: CliRunner, live_pool: StoragePool) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_pool._hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, 'pool', 'xml', live_pool.name))
    assert result.exit_code == 0
    assert len(result.output) > 0

    output_xml = etree.XML(result.output)
    pool_xml = live_pool.config

    compare_xml_trees(pool_xml, output_xml)
