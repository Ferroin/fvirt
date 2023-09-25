# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Domain related commands for the virshx CLI interface.'''

from __future__ import annotations

import click

from .define import define
from .list import list_domains
from .reset import reset
from .shutdown import shutdown
from .start import start
from .stop import stop
from .xslt import xslt


@click.group
@click.pass_context
def domain(ctx: click.core.Context) -> None:
    '''Perform various operations on libvirt domains.'''


domain.add_command(define)
domain.add_command(list_domains)
domain.add_command(reset)
domain.add_command(shutdown)
domain.add_command(start)
domain.add_command(stop)
domain.add_command(xslt)

__all__ = [
    'domain',
]
