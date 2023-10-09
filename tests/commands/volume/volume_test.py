# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.volume'''

from click.testing import CliRunner

from fvirt.cli import cli


def test_lazy_load() -> None:
    '''Test that lazy loading is working at a basic level.

       Also checks the help command.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['volume', 'help'])
    assert result.exit_code == 0
