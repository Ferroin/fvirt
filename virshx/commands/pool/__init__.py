# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Storage pool related commands for the virshx CLI interface.'''

from __future__ import annotations

import click

from .list import list_pools
from .start import start
from .stop import stop
from .xslt import xslt


@click.group
@click.pass_context
def pool(ctx: click.core.Context) -> None:
    '''Perform various operations on libvirt storage pools.'''


pool.add_command(list_pools)
pool.add_command(start)
pool.add_command(stop)
pool.add_command(xslt)

__all__ = [
    'pool',
]
