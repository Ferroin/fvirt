# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to gracefully shut down domains.'''

from __future__ import annotations

from typing import Self

import click

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from ...libvirt.domain import MATCH_ALIASES


class _ShutdownCommand(SimpleLifecycleCommand):
    '''Command for shutting down libvirt domains.'''
    @property
    def METHOD(self: Self) -> str: return 'shutdown'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='shut down',
            continuous='shutting down',
            past='shut down',
            idempotent_state='shut down',
        )


shutdown = _ShutdownCommand(
    name='shutdown',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    doc_name='domain',
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
