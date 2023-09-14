# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import click

from ..libvirt import Hypervisor
from ..libvirt.volume import MATCH_ALIASES
from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, matcher, print_match_help
from ..util.tables import render_table, Column, ColumnsParam, print_columns, tabulate_entities

if TYPE_CHECKING:
    import re

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
@click.option('--match', type=(MatchTargetParam(MATCH_ALIASES)(), MatchPatternParam()),
              help='Limit listed domains by match parameter. For more info, use `--match-help`')
@click.option('--match-help', is_flag=True, default=False,
              help='Show help info about object matching.')
@click.argument('pool', nargs=1, required=True)
@click.pass_context
def volumes(
        ctx: click.core.Context,
        columns: list[str],
        match: tuple[MatchTarget, re.Pattern] | None,
        match_help: bool,
        pool: str,
        ) -> None:
    '''List volumes in a given storage pool.

       This will produce a (reasonably) nicely formatted table of volumes
       in the specified storage pool, possibly limited by the specified
       matching parameters.'''
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
        storage_pool = hv.pools_by_name[pool]
        volumes = filter(select, storage_pool.volumes)
        data = tabulate_entities(volumes, COLUMNS, columns)

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
