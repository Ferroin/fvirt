# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to print the host libvirt version.'''

from __future__ import annotations

from typing import Final

import click

from .._base.command import Command
from .._base.state import State

HELP: Final = '''
Print the host system libvirt version information.

This will output two lines, one for the libvirt version on the target
host, and one for the underlying hypervisor version.

For client-only drivers, the libvirt version should match the local
libvirt version. For other drivers, it should be the version of the
libvirtd instance you are connecting to.

Depending on the hypervisor driver in use, the hypervisor version may not
be reported, in which case this command will show a version of UNKNOWN.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    with state.hypervisor as hv:
        click.echo(f'libvirt: v{ str(hv.lib_version) }')

        if hv.uri.driver is not None:
            driver = hv.uri.driver.value
        else:
            driver = 'unknown'

        if hv.version is None:
            version = 'UNKNOWN'
        else:
            version = f'v{ str(hv.version) }'

        click.echo(f'Hypervisor ({ driver }): { version }')


version: Final = Command(
    name='version',
    help=HELP,
    callback=cb,
)

__all__ = [
    'version',
]
