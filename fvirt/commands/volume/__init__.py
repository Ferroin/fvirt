# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Volume related commands for the fvirt CLI interface.'''

from __future__ import annotations

import click

from .define import define
from .list import list_volumes

from ...libvirt.volume import MATCH_ALIASES
from ...util.commands import make_help_command
from ...util.match_params import make_alias_help


@click.group(short_help='Perform various operations on libvirt volumes.')
@click.pass_context
def volume(ctx: click.core.Context) -> None:
    '''Perform various operations on libvirt volumes.

       Each volume is inherently part of a specific storage pool. All
       of the volume subcommands require specifying the pool name with
       the POOL argument.'''


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
