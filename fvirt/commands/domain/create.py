# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create a new domain.'''

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from .._base.command import Command
from ...libvirt import InsufficientPrivileges, InvalidConfig

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .._base.state import State

HELP = '''
Create one or more new transient domains.

The CONFIGPATH argument should point to one or more valid XML
configurations for a domain. If more than one CONFIGPATH is specified,
each should correspond to a separate domain to be created.

If a specified configuration describes a domain that already
exists, it will silently overwrite the the existing configuration
for that domain.

All specified configuration files will be read prior to attempting to
create any domains. Thus, if any configuration file cannot be read,
no domains will be created.

If more than one domain is requested to be created, a failure
creating any domain will result in a non-zero exit code even if
some domains were created.

This command supports fvirt's fail-fast logic. In fail-fast mode,
the first domain that fails to be created will cause the operation
to stop, and any failure will result in a non-zero exit code.

This command does not support fvirt's idempotent mode.
'''.lstrip().rstrip()


def cb(
        ctx: click.Context,
        state: State,
        confpath: Sequence[str],
        paused: bool,
        reset_nvram: bool,
) -> None:
    success = 0

    confdata = []

    for cpath in confpath:
        with click.open_file(cpath, mode='r') as config:
            confdata.append(config.read())

    with state.hypervisor as hv:
        for conf in confdata:
            try:
                entity = hv.createDomain(conf, paused=paused, reset_nvram=reset_nvram)
            except InsufficientPrivileges:
                ctx.fail('Specified hypervisor connection is read-only, unable to create domain')
            except InvalidConfig:
                click.echo(f'The configuration at { cpath } is not valid for a domain.')

                if state.fail_fast:
                    break

            click.echo(f'Successfully created domain: { entity.name }')
            success += 1

    click.echo('Finished creating specified domains.')
    click.echo('')
    click.echo('Results:')
    click.echo(f'  Success:     { success }')
    click.echo(f'  Failed:      { len(confdata) - success }')
    click.echo(f'Total:         { len(confdata) }')

    if success != len(confdata) and confdata:
        ctx.exit(3)


create = Command(
    name='create',
    callback=cb,
    help=HELP,
    params=(
        click.Option(
            param_decls=('--paused',),
            is_flag=True,
            default=False,
            help='Start the domain in paused state instead of running it immediately.',
        ),
        click.Option(
            param_decls=('--reset-nvram',),
            is_flag=True,
            default=False,
            help='Reset any existing NVRAM state before starting the domain.',
        ),
        click.Argument(
            param_decls=('confpath',),
            type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
            nargs=-1,
        ),
    ),
)

__all__ = [
    'create',
]
