# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Domain related commands for the fvirt CLI interface.'''

from __future__ import annotations

import click

from .create import create
from .define import define
from .list import list_domains
from .reset import reset
from .shutdown import shutdown
from .start import start
from .stop import stop
from .undefine import undefine
from .xslt import xslt

from ...libvirt.domain import MATCH_ALIASES
from ...util.commands import make_help_command
from ...util.match import make_alias_help


@click.group(short_help='Perform various operations on libvirt domains.')
@click.pass_context
def domain(ctx: click.core.Context) -> None:
    '''Perform various operations on libvirt domains.'''


domain.add_command(create)
domain.add_command(define)
domain.add_command(list_domains)
domain.add_command(reset)
domain.add_command(shutdown)
domain.add_command(start)
domain.add_command(stop)
domain.add_command(undefine)
domain.add_command(xslt)

domain.add_command(make_help_command(domain, 'domain', {
    'aliases': (
        'List recognized match aliases for matching domains.',
        make_alias_help(MATCH_ALIASES, 'domain'),
    ),
}))

__all__ = [
    'domain',
]
