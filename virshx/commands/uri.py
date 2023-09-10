# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to print the hypervisor URI in use.'''

from __future__ import annotations

import click

from ..libvirt import Hypervisor


@click.command
@click.pass_context
def uri(ctx: click.core.Context) -> None:
    '''print the hypervisor URI'''
    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        click.echo(str(hv.uri))


__all__ = [
    'uri',
]
