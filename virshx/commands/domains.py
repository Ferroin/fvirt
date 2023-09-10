# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list domains.'''

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ..libvirt import Hypervisor, Domain, DomainState
from ..common import render_table, Column, ColumnsParam, color_bool, TERM

if TYPE_CHECKING:
    from collections.abc import Iterable


def color_state(state: DomainState) -> str:
    '''Apply colors to a domain state.'''
    match state:
        case d if d in {DomainState.RUNNING}:
            return TERM.bright_green(TERM.on_black(str(state)))
        case d if d in {DomainState.CRASHED, DomainState.BLOCKED, DomainState.NONE}:
            return TERM.bright_red(TERM.on_black(str(state)))
        case d if d in {DomainState.PAUSED}:
            return TERM.bright_yellow(TERM.on_black(str(state)))
        case d if d in {DomainState.PMSUSPEND}:
            return TERM.bright_blue(TERM.on_black(str(state)))
        case _:
            return str(state)

    raise RuntimeError  # Needed because mypy thinks the above case statement is non-exhaustive.


def format_id(value: int) -> str:
    if value == -1:
        return '-'
    else:
        return str(value)


COLUMNS = {
    'name': Column(title='Name', prop='name'),
    'id': Column(title='ID', prop='id', right_align=True, color=format_id),
    'uuid': Column(title='UUID', prop='uuid'),
    'state': Column(title='State', prop='state', color=color_state),
    'persistent': Column(title='Is Persistent', prop='persistent', color=color_bool),
    'managed-save': Column(title='Has Managed Save', prop='hasManagedSave', color=color_bool),
    'current-snapshot': Column(title='Has Current Snapshot', prop='hasCurrentSnapshot', color=color_bool),
    'title': Column(title='Domain Title', prop='title'),
}

DEFAULT_COLS = [
    'id',
    'name',
    'state',
]


def tabulate_domains(domains: Iterable[Domain], cols: list[str] = DEFAULT_COLS) -> list[list[str]]:
    '''Convert a list of domains to a list of values for columns.'''
    ret = []

    for domain in domains:
        items = []

        for column in cols:
            prop = getattr(domain, COLUMNS[column].prop)

            if hasattr(prop, '__get__'):
                prop = prop.__get__(domain)

            items.append(prop)

        ret.append(items)

    return ret


@click.command
@click.option('--columns', type=ColumnsParam(COLUMNS, 'domain columns')(), nargs=1,
              help='A comma separated list of columns to show when listing domains.',
              default=DEFAULT_COLS)
@click.pass_context
def domains(ctx: click.core.Context, columns: list[str]) -> None:
    '''list domains'''
    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        data = tabulate_domains(hv.domains, columns)

    output = render_table(
        data,
        [COLUMNS[x] for x in columns],
    )

    click.echo(output)


__all__ = [
    'domains',
]
