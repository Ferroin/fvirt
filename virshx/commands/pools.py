# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from ..libvirt import Hypervisor
from ..libvirt.storage_pool import MATCH_ALIASES
from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, matcher, print_match_help
from ..util.tables import render_table, Column, ColumnsParam, color_bool, print_columns, tabulate_entities
from ..util.terminal import TERM

if TYPE_CHECKING:
    import re


def color_state(value: bool) -> str:
    '''Apply colors to a pool state.'''
    if value:
        return TERM.bright_green_on_black('running')
    else:
        return 'inactive'


COLUMNS = {
    'name': Column(title='Name', prop='name'),
    'uuid': Column(title='UUID', prop='uuid'),
    'state': Column(title='State', prop='running', color=color_state),
    'persistent': Column(title='Persistent', prop='persistent', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
    'volumes': Column(title='Volumes', prop='numVolumes', right_align=True),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True),
    'allocation': Column(title='Allocation', prop='allocation', right_align=True),
    'available': Column(title='Available', prop='available', right_align=True),
    'type': Column(title='Type', prop='type'),
    'format': Column(title='Format', prop='format'),
    'dir': Column(title='Directory', prop='dir'),
    'device': Column(title='Device', prop='device'),
    'target': Column(title='Target', prop='target'),
}

DEFAULT_COLS = [
    'name',
    'type',
    'format',
    'state',
    'autostart',
    'volumes',
    'capacity',
    'available',
]


@click.command
@click.option('--columns', type=ColumnsParam(COLUMNS, 'storage pool columns')(), nargs=1,
              help='A comma separated list of columns to show when listing storage pools. Use `--columns list` to list recognized column names.',
              default=DEFAULT_COLS)
@click.option('--match', type=(MatchTargetParam(MATCH_ALIASES)(), MatchPatternParam()),
              help='Limit listed storage pools by match parameter. For more info, use `--match-help`')
@click.option('--match-help', is_flag=True, default=False,
              help='Show help info about object matching.')
@click.pass_context
def pools(
        ctx: click.core.Context,
        columns: list[str],
        match: tuple[MatchTarget, re.Pattern] | None,
        match_help: bool,
        ) -> None:
    '''List storage pools.

       This will produce a (reasonably) nicely formatted table of storage pools,
       possibly limited by the specified matching parameters.'''
    if columns == ['list']:
        print_columns(COLUMNS, DEFAULT_COLS)
        ctx.exit(0)

    if match_help:
        print_match_help(MATCH_ALIASES)
        ctx.exit(0)

    if match is not None:
        select = matcher(*match)
    else:
        def select(x: Any) -> bool: return True

    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        pools = filter(select, hv.pools)

        data = tabulate_entities(pools, COLUMNS, columns)

    output = render_table(
        data,
        [COLUMNS[x] for x in columns],
    )

    click.echo(output)


__all__ = [
    'pools',
]
