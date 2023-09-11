# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

import click

from ..libvirt import Hypervisor
from ..common import render_table, Column, ColumnsParam, color_bool, print_columns, tabulate_entities, TERM


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
    'persistent': Column(title='Is Persistent', prop='persistent', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
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
    'state',
    'autostart',
]


@click.command
@click.option('--columns', type=ColumnsParam(COLUMNS, 'storage pool columns')(), nargs=1,
              help='A comma separated list of columns to show when listing storage pools. Use `--columns list` to list recognized column names.',
              default=DEFAULT_COLS)
@click.pass_context
def pools(ctx: click.core.Context, columns: list[str]) -> None:
    '''list storage pools'''
    if columns == ['list']:
        print_columns(COLUMNS, DEFAULT_COLS)
        ctx.exit(0)

    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        data = tabulate_entities(hv.pools, COLUMNS, columns)

    output = render_table(
        data,
        [COLUMNS[x] for x in columns],
    )

    click.echo(output)


__all__ = [
    'COLUMNS',
    'DEFAULT_COLS',
]
