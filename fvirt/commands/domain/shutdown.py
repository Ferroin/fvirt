# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to gracefully shut down domains.'''

from __future__ import annotations

from typing import cast

import click

from .._base.lifecycle import LifecycleCommand, OperationHelpInfo

from ...libvirt import LifecycleResult, Domain
from ...libvirt.entity import Entity
from ...libvirt.domain import MATCH_ALIASES


def callback(ctx: click.Context, domain: Entity, /, *, timeout: int, force: bool) -> LifecycleResult:
    return cast(Domain, domain).shutdown(timeout=timeout, force=force, idempotent=ctx.obj['idempotent'])


shutdown = LifecycleCommand(
    name='shutdown',
    aliases=MATCH_ALIASES,
    callback=callback,
    hvprop='domains',
    doc_name='domain',
    op_help=OperationHelpInfo(
        verb='shut down',
        continuous='shutting down',
        past='shut down',
        idempotent_state='shut down',
    ),
    params=(
        click.Option(
            param_decls=('--timeout',),
            type=click.IntRange(min=0),
            default=0,
            metavar='TIMEOUT',
            help='Specify a timeout in seconds within which the domain must shut down. A value of 0 means no timeout.',
        ),
        click.Option(
            param_decls=('--force',),
            is_flag=True,
            default=False,
            help='If a domain fails to shut down within the specified timeout, forcibly stop it.',
        ),
    ),
)

__all__ = [
    'shutdown',
]
