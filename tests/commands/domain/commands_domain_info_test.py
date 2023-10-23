# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.info'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.cli import cli
from fvirt.commands.domain.info import INFO_ITEMS

from ..shared import check_info_items, check_info_output

if TYPE_CHECKING:
    from click.testing import CliRunner

    from fvirt.libvirt import Domain, Hypervisor


def test_info_items(test_dom: Domain) -> None:
    '''Test that the defined info items are valid.'''
    check_info_items(INFO_ITEMS, test_dom)


def test_command_run(cli_runner: CliRunner, test_hv: Hypervisor) -> None:
    '''Test that the command runs correctly.'''
    uri = str(test_hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, 'domain', 'info', '1'))
    assert result.exit_code == 0
    assert len(result.output) > 0

    dom = test_hv.domains.get(1)
    assert dom is not None

    check_info_output(result.output, INFO_ITEMS, dom, 'Domain: 1')
