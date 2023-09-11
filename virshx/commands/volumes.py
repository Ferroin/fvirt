# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

import click

from ..libvirt import Hypervisor
from ..util.tables import render_table, Column, ColumnsParam, print_columns, tabulate_entities


COLUMNS = {
    'name': Column(title='Name', prop='name'),
    'key': Column(title='Key', prop='key'),
    'type': Column(title='Type', prop='type'),
    'format': Column(title='Format', prop='format'),
    'path': Column(title='Path', prop='path'),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True),
    'allocation': Column(title='Allocation', prop='allocation', right_align=True),
}

DEFAULT_COLS = [
    'name',
    'path',
    'capacity',
]


@click.command
@click.option('--columns', type=ColumnsParam(COLUMNS, 'volume columns')(), nargs=1,
              help='A comma separated list of columns to show when listing volumes. Use `--columns list` to list recognized column names.',
              default=DEFAULT_COLS)
@click.argument('pool', nargs=1, required=True)
@click.pass_context
def volumes(ctx: click.core.Context, columns: list[str], pool: str) -> None:
    '''list volumes'''
    if columns == ['list']:
        print_columns(COLUMNS, DEFAULT_COLS)
        ctx.exit(0)

    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        storage_pool = hv.pools_by_name[pool]
        data = tabulate_entities(storage_pool.volumes, COLUMNS, columns)

    output = render_table(
        data,
        [COLUMNS[x] for x in columns],
    )

    click.echo(output)


__all__ = [
    'COLUMNS',
    'DEFAULT_COLS',
    'volumes',
]
