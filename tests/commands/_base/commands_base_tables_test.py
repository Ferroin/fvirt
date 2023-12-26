# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.tables'''

from __future__ import annotations

import re

from itertools import combinations
from traceback import format_exception
from typing import TYPE_CHECKING, Any

import click
import pytest

from fvirt.commands._base.objects import DisplayProperty
from fvirt.commands._base.tables import ColumnsParam, color_bool, color_optional, column_info, render_table, tabulate_entities

if TYPE_CHECKING:
    from collections.abc import Sequence

    from click.testing import CliRunner

    from fvirt.libvirt import Domain, Hypervisor

TEST_COLUMNS = {
    'name': DisplayProperty(title='Name', name='Name', prop='name'),
    'uuid': DisplayProperty(title='UUID', name='UUID', prop='uuid'),
    'running': DisplayProperty(title='Running', name='Running', prop='running', color=color_bool),
    'id': DisplayProperty(title='ID', name='ID', prop='id', color=str, right_align=True),
}

DEFAULT_COLS = (
    'name',
    'id',
)

TEST_LINES = [
    ['a', 'b', True, 1],
    ['c', 'd', False, -1],
]

SELECTED_TEST_COLUMNS = [
    TEST_COLUMNS['name'],
    TEST_COLUMNS['uuid'],
    TEST_COLUMNS['running'],
    TEST_COLUMNS['id'],
]


@pytest.fixture(scope='session')
def column_test_cmd() -> click.Command:
    '''Provide a command for testing the ColumnsParam constructor.'''
    @click.command
    @click.option('--columns', type=ColumnsParam(TEST_COLUMNS, 'columns')())
    def test(columns: Sequence[str]) -> None:
        for col in columns:
            click.echo(col)

    return test


@pytest.mark.parametrize('i, e', (
    (True, 'Yes'),
    (False, 'No'),
))
def test_color_bool(i: bool, e: str) -> None:
    '''Check that the color_bool function renders booleans correctly.'''
    result = color_bool(i)

    assert isinstance(result, str)
    assert e in result


@pytest.mark.parametrize('i, e', (
    (None, '-'),
    ('-', '-'),
    (1, '1'),
    ('', ''),
))
def test_color_optional(i: Any, e: str) -> None:
    '''Check that the color_optional function renders things correctly.'''
    result = color_optional(i)

    assert isinstance(result, str)
    assert result == e


def test_column_info() -> None:
    '''Test the output of the column info function.'''
    results = column_info(TEST_COLUMNS, DEFAULT_COLS)

    assert isinstance(results, str)

    resultlines = results.splitlines()

    for key in TEST_COLUMNS.keys():
        assert f'  - { key }' in resultlines

    for col in DEFAULT_COLS:
        assert col in resultlines[-1]


@pytest.mark.parametrize('cols', [[x] for x in TEST_COLUMNS.keys()] +
                                 [x for x in combinations(TEST_COLUMNS.keys(), 2)] +
                                 [x for x in combinations(TEST_COLUMNS.keys(), 3)] +
                                 [[x for x in TEST_COLUMNS.keys()]])
def test_tabulate_entities(test_dom: tuple[Domain, Hypervisor], cols: Sequence[str]) -> None:
    '''Test the tabulate_entities function.'''
    dom, _ = test_dom
    results = tabulate_entities([dom], TEST_COLUMNS, cols)

    assert len(results) == 1

    for idx, col in enumerate(cols):
        assert results[0][idx] == getattr(dom, TEST_COLUMNS[col].prop)


def test_render_table_without_titles() -> None:
    '''Test rendering tables without titles included.'''
    results = render_table(
        TEST_LINES,
        SELECTED_TEST_COLUMNS,
        headings=False,
    )

    assert isinstance(results, str)

    result_lines = results.splitlines()

    assert len(result_lines) == len(TEST_LINES)

    for i in range(0, len(result_lines)):
        items = result_lines[i].split()

        assert len(items) == len(TEST_LINES[i])

        for j in range(0, len(items)):
            assert items[j] == SELECTED_TEST_COLUMNS[j].color(TEST_LINES[i][j])


def test_render_table_with_titles() -> None:
    '''Test rendering tables with titles included.'''
    results = render_table(
        TEST_LINES,
        SELECTED_TEST_COLUMNS,
        headings=True,
    )

    assert isinstance(results, str)

    result_lines = results.splitlines()

    assert len(result_lines) == (len(TEST_LINES) + 2)

    titles = result_lines[0].split()

    assert len(titles) == len(SELECTED_TEST_COLUMNS)

    for i in range(0, len(titles)):
        assert titles[i] == SELECTED_TEST_COLUMNS[i].title

    assert re.match('^-+$', result_lines[1]) is not None

    for i in range(2, len(result_lines)):
        items = result_lines[i].split()

        assert len(items) == len(TEST_LINES[i - 2])

        for j in range(0, len(items)):
            assert items[j] == SELECTED_TEST_COLUMNS[j].color(TEST_LINES[i - 2][j])


def test_columns_param_list(cli_runner: CliRunner, column_test_cmd: click.Command) -> None:
    '''Test list functionality of ColumnsParam.'''
    result = cli_runner.invoke(column_test_cmd, ['--columns', 'list'])
    assert not result.exception, ''.join(format_exception(*result.exc_info))  # type: ignore
    assert result.exit_code == 0, result.output

    output_lines = result.output.splitlines()

    assert len(output_lines) == 1
    assert re.match('^list$', output_lines[0])


def test_columns_param_all(cli_runner: CliRunner, column_test_cmd: click.Command) -> None:
    '''Test all columns functionality of ColumnsParam.'''
    result = cli_runner.invoke(column_test_cmd, ['--columns', 'all'])
    assert not result.exception, ''.join(format_exception(*result.exc_info))  # type: ignore
    assert result.exit_code == 0, result.output

    output_lines = result.output.splitlines()

    assert len(output_lines) == len(TEST_COLUMNS)

    assert {x for x in output_lines} == {x for x in TEST_COLUMNS.keys()}


@pytest.mark.parametrize('cols', [[x] for x in TEST_COLUMNS.keys()] +
                                 [x for x in combinations(TEST_COLUMNS.keys(), 2)] +
                                 [x for x in combinations(TEST_COLUMNS.keys(), 3)] +
                                 [[x for x in TEST_COLUMNS.keys()]])
def test_columns_param(cli_runner: CliRunner, column_test_cmd: click.Command, cols: Sequence[str]) -> None:
    '''Test column selection functionality of ColumnsParam.'''
    result = cli_runner.invoke(column_test_cmd, ['--columns', ', '.join(cols)])
    assert not result.exception, ''.join(format_exception(*result.exc_info))  # type: ignore
    assert result.exit_code == 0, result.output

    output_lines = result.output.splitlines()

    assert len(output_lines) == len(cols)

    assert {x for x in output_lines} == {x for x in cols}
