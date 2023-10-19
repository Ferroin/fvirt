# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create a new domain.'''

from __future__ import annotations

from typing import Final, final

import click

from .._base.new import CreateCommand
from .._base.objects import DomainMixin


@final
class _DomainCreate(CreateCommand, DomainMixin):
    pass


create: Final = _DomainCreate(
    name='create',
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
    ),
)

__all__ = [
    'create',
]
