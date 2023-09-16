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
@click.option('--fail-fast/--no-fail-fast', default=False,
              help='If operating on multiple objects, fail as soon as one operation fails instead of attempting all operations.')
@click.option('--idempotent/--no-idempotent', default=True,
              help='Make operations idempotent when possible.')
@click.option('--fail-if-no-match/--no-fail-if-no-match', default=False,
              help='If using the --match option, return with a non-zero exit status if no match is found.')
@click.pass_context
def cli(
        ctx: click.core.Context,
        connect: str,
        fail_fast: bool,
        idempotent: bool,
        fail_if_no_match: bool,
        ) -> None:
    '''Extra tooling to supplemnt virsh.'''
    ctx.ensure_object(dict)
    ctx.obj['uri'] = URI.from_string(connect)
    ctx.obj['fail_fast'] = fail_fast
    ctx.obj['idempotent'] = idempotent
    ctx.obj['fail_if_no_match'] = fail_if_no_match


for cmd in COMMANDS:
    cli.add_command(cmd)

__all__ = [
    'cli',
]
