# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''CLI interface for virshx.'''

from __future__ import annotations

import click

from .libvirt import API_VERSION, URI
from .version import VERSION
from .commands import COMMANDS


@click.group
@click.version_option(version=f'{ VERSION }, using libvirt-python { API_VERSION }')
@click.option('--connect', '-c', '--uri', nargs=1, type=str, default='', help='hypervisor connection URI', metavar='URI')
@click.pass_context
def cli(
        ctx: click.core.Context,
        connect: str,
        ) -> None:
    '''Extra tooling to supplemnt virsh.'''
    ctx.ensure_object(dict)
    ctx.obj['uri'] = URI.from_string(connect)


for cmd in COMMANDS:
    cli.add_command(cmd)

__all__ = [
    'cli',
]
