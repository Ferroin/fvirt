# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Volume related commands for the virshx CLI interface.'''

from __future__ import annotations

import click

from .list import list_volumes


@click.group
@click.argument('pool', nargs=1, required=True)
@click.pass_context
def volume(ctx: click.core.Context, pool: str) -> None:
    '''Perform various operations on libvirt volumes.

       Each volume is inherently part of a specific storage pool. All
       of the volume subcommands require specifying the pool name with
       the POOL argument.

       Note that the POOL argument _must_ come before the subcommand,
       not after it.'''
    ctx.obj['pool'] = pool


volume.add_command(list_volumes)

__all__ = [
    'volume',
]
