# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list domains.'''

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ..libvirt import Hypervisor, Domain
from ..common import render_table, Column

if TYPE_CHECKING:
    from collections.abc import Iterable

COLUMNS = {
    'name': Column(title='Name', prop='name'),
    'id': Column(title='ID', prop='id', right_align=True),
    'uuid': Column(title='UUID', prop='uuid'),
    'state': Column(title='State', prop='state'),
    'persistent': Column(title='Is Persistent', prop='persistent'),
    'managed-save': Column(title='Has Managed Save', prop='hasManagedSave'),
    'current-snapshot': Column(title='Has Current Snapshot', prop='hasCurrentSnapshot'),
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

            items.append(str(prop))

        ret.append(items)

    return ret


@click.command
@click.pass_context
def domains(ctx: click.core.Context) -> None:
    '''list domains'''
    columns = DEFAULT_COLS

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
