# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to print the hypervisor URI in use.'''

from __future__ import annotations

import click

from ._base.command import Command
from ._base.state import State

HELP = '''
Print the hypervisor URI.

This functions identically to the virsh `uri` command, except it uses
the fvirt.libvirt bindings.

For more information about how fvirt handles libvirt URIs, run `fvirt
help connections`.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    with state.hypervisor as hv:
        click.echo(str(hv.uri))


uri = Command(
    name='uri',
    help=HELP,
    callback=cb,
)

__all__ = [
    'uri',
]
