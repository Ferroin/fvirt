# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.list'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.cli import cli
from fvirt.commands.domain.list import COLUMNS, DEFAULT_COLS

from ..shared import check_columns, check_default_columns, check_list_entry, check_list_output

if TYPE_CHECKING:
    from collections.abc import Sequence

    from click.testing import CliRunner

    from fvirt.libvirt import Domain, Hypervisor


def test_column_definitions(test_dom: Domain) -> None:
    '''Test that column definitions are valid.'''
    check_columns(COLUMNS, test_dom)


def test_default_columns() -> None:
    '''Test that the default column list is valid.'''
    check_default_columns(COLUMNS, DEFAULT_COLS)


def test_list(cli_runner: CliRunner, test_hv: Hypervisor) -> None:
    '''Test the list command.'''
    uri = str(test_hv.uri)
    dom = test_hv.domains.get(1)
    assert dom is not None

    result = cli_runner.invoke(cli, ('-c', uri, '--units', 'bytes', 'domain', 'list'))
    assert result.exit_code == 0

    check_list_output(result.output, dom, tuple(COLUMNS[x] for x in DEFAULT_COLS))


def test_no_headings(cli_runner: CliRunner, test_hv: Hypervisor) -> None:
    '''Test the --no-headings option.'''
    uri = str(test_hv.uri)
    dom = test_hv.domains.get(1)
    assert dom is not None

    result = cli_runner.invoke(cli, ('-c', uri, '--units', 'bytes', 'domain', 'list', '--no-headings'))
    assert result.exit_code == 0

    check_list_entry(result.output, dom, tuple(COLUMNS[x] for x in DEFAULT_COLS))


@pytest.mark.parametrize('a, e', (
    ('name', ('test',)),
    ('uuid', ('6695eb01-f6a4-8304-79aa-97f2502e193f',)),
    ('id', ('1',)),
))
def test_list_only(cli_runner: CliRunner, test_uri: str, a: str, e: Sequence[str]) -> None:
    '''Test that the --only option works correctly.'''
    result = cli_runner.invoke(cli, ('-c', test_uri, 'domain', 'list', '--only', a))
    assert result.exit_code == 0

    assert set(e) == set(result.output.splitlines())
