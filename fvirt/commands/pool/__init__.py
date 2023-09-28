# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Storage pool related commands for the fvirt CLI interface.'''

from __future__ import annotations

import click

from .define import define
from .list import list_pools
from .start import start
from .stop import stop
from .undefine import undefine
from .xslt import xslt

from ...libvirt.volume import MATCH_ALIASES
from ...util.commands import make_help_command
from ...util.match import make_alias_help


@click.group
@click.pass_context
def pool(ctx: click.core.Context) -> None:
    '''Perform various operations on libvirt storage pools.'''


pool.add_command(define)
pool.add_command(list_pools)
pool.add_command(start)
pool.add_command(stop)
pool.add_command(undefine)
pool.add_command(xslt)

pool.add_command(make_help_command(pool, 'pool', {
    'aliases': (
        'List recognized match aliases for matching with storage pools.',
        make_alias_help(MATCH_ALIASES, 'pool'),
    ),
}))

__all__ = [
    'pool',
]
