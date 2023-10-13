# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host.uri'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_uri(cli_runner: CliRunner, test_uri: str) -> None:
    '''Test that the host uri command properly reports the URI.'''
    result = cli_runner.invoke(cli, ['-c', test_uri, 'host', 'uri'])
    assert result.exit_code == 0
    assert result.output == f'{ test_uri }\n'
