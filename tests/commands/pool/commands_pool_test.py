# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.pool'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.cli import cli
from fvirt.commands.pool import pool

from ..shared import SRC_ROOT, check_lazy_commands

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_lazy_load(cli_runner: CliRunner) -> None:
    '''Test that lazy loading is working at a basic level.

       Also checks the help command.'''
    result = cli_runner.invoke(cli, ['pool', 'help'])
    assert result.exit_code == 0


def test_check_lazy_command_list() -> None:
    '''Further checks for lazy loading of commands.'''
    check_lazy_commands(pool, SRC_ROOT / 'fvirt' / 'commands' / 'pool')


def test_help_aliases(cli_runner: CliRunner) -> None:
    '''Check that we have an aliases help topic.'''
    # TODO: Should be extended to cross-check against alias list.
    result = cli_runner.invoke(cli, ('pool', 'help', 'aliases'))
    assert result.exit_code == 0
