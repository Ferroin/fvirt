# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''CLI interface for virshx.'''

from __future__ import annotations

import click

from .libvirt import API_VERSION
from .common import VERSION
from .commands import COMMANDS


@click.group
@click.version_option(version=f'{ VERSION }, using libvirt-python { API_VERSION }')
@click.pass_context
def cli(ctx: click.core.Context) -> None:
    '''Extra tooling to supplemnt virsh.'''
    ctx.ensure_object(dict)


for cmd in COMMANDS:
    cli.add_command(cmd)

__all__ = [
    'cli',
]
