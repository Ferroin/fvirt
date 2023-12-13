# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create new domains.'''

from __future__ import annotations

from typing import Final, final

import click

from .._base.new import NewCommand
from .._base.objects import DomainMixin


@final
class _NewDomain(NewCommand, DomainMixin):
    pass


new: Final = _NewDomain(
    params=(
        click.Option(
            param_decls=('--paused',),
            is_flag=True,
            default=False,
            help='Start the domain in paused state instead of running it immediately. Only supported with `--create`.',
        ),
        click.Option(
            param_decls=('--reset-nvram',),
            is_flag=True,
            default=False,
            help='Reset any existing NVRAM state before starting the domain. Only supported with `--create`.',
        ),
    ),
    define_params=tuple(),
    create_params=(
        'paused',
        'reset_nvram',
    ),
)

__all__ = [
    'new',
]
