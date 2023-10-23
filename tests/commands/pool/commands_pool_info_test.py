# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.info'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.cli import cli
from fvirt.commands.pool.info import INFO_ITEMS

from ..shared import check_info_items, check_info_output

if TYPE_CHECKING:
    from click.testing import CliRunner

    from fvirt.libvirt.storage_pool import StoragePool


def test_info_items(test_pool: StoragePool) -> None:
    '''Test that the defined info items are valid.'''
    check_info_items(INFO_ITEMS, test_pool)


def test_command_run(cli_runner: CliRunner, live_pool: StoragePool) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_pool._hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, 'pool', 'info', live_pool.name))
    assert result.exit_code == 0
    assert len(result.output) > 0

    check_info_output(result.output, INFO_ITEMS, live_pool, f'Storage Pool: { live_pool.name }')
