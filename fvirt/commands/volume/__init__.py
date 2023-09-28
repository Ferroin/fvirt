# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Volume related commands for the fvirt CLI interface.'''

from __future__ import annotations

import click

from .define import define
from .list import list_volumes

from ...libvirt.volume import MATCH_ALIASES
from ...util.commands import make_help_command
from ...util.match import make_alias_help


@click.group
@click.argument('pool', nargs=1, required=True)
@click.pass_context
def volume(ctx: click.core.Context, pool: str) -> None:
    '''Perform various operations on libvirt volumes.

       Each volume is inherently part of a specific storage pool. All
       of the volume subcommands require specifying the pool name with
       the POOL argument.

       See the pool command for operations on storage pools instead
       of volumes.

       Note that the POOL argument _must_ come before the subcommand,
       not after it.'''
    ctx.obj['pool'] = pool


volume.add_command(define)
volume.add_command(list_volumes)

volume.add_command(make_help_command(volume, 'volume', {
    'aliases': (
        'List recognized match aliases for matching volumes.',
        make_alias_help(MATCH_ALIASES, 'volume'),
    ),
}))

__all__ = [
    'volume',
]
