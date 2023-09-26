# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create a new domain.'''

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ...libvirt import Hypervisor, InsufficientPrivileges, InvalidConfig

if TYPE_CHECKING:
    from collections.abc import Sequence


@click.command
@click.argument('confpath', nargs=-1)
@click.option('--paused', is_flag=True, default=False,
              help='Start the domain in paused state instead of running it immediately.''')
@click.option('--reset-nvram', is_flag=True, default=False,
              help='Reset any existing NVRAM state before starting the domain.''')
@click.pass_context
def create(
        ctx: click.core.Context,
        confpath: Sequence[str],
        paused: bool,
        reset_nvram: bool,
        ) -> None:
    '''Create one or more new transient domains.

       The CONFIGPATH argument should point to a valid XML configuration
       for a domain. If more than one CONFIGPATH is specified, each
       should correspond to a separate domain to be created.

       If a specified configuration describes a domain that already
       exists, it will silently overwrite the the existing configuration
       for that domain.

       If more than one domain is requested to be created, a failure
       creating any domain will result in a non-zero exit code even if
       some domains were created.

       This command supports virshx's fail-fast logic. In fail-fast mode,
       the first domain that fails to be created will cause the operation
       to stop, and any failure will result in a non-zero exit code.

       This command does not support virshx's idempotent mode.'''
    success = 0

    for cpath in confpath:
        with click.open_file(cpath, mode='r') as config:
            confdata = config.read()

        with Hypervisor(hvuri=ctx.obj['uri']) as hv:
            try:
                entity = hv.createDomain(confdata, paused=paused, reset_nvram=reset_nvram)
            except InsufficientPrivileges:
                ctx.fail('Specified hypervisor connection is read-only, unable to create domain')
            except InvalidConfig:
                click.echo(f'The configuration at { cpath } is not valid for a domain.')

                if ctx.obj['fail_fast']:
                    break

            click.echo(f'Successfully created domain: { entity.name }')
            success += 1

    if success or (not confpath):
        click.echo(f'Successfully createded { success } out of { len(confpath) } domains.')

        if success != len(confpath):
            ctx.exit(3)
    else:
        click.echo('Failed to create any domains.')
        ctx.exit(3)


__all__ = [
    'create',
]
