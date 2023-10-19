# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create a new storage pool.'''

from __future__ import annotations

from typing import Final, final

import click

from .._base.new import CreateCommand
from .._base.objects import StoragePoolMixin


@final
class _PoolCreate(CreateCommand, StoragePoolMixin):
    pass


create: Final = _PoolCreate(
    name='create',
    params=(
        click.Option(
            param_decls=('--build',),
            is_flag=True,
            default=False,
            help='Build the storage pool while creating it.',
        ),
        click.Option(
            param_decls=('--overwrite/--no-overwrite',),
            default=None,
            help='Control whether any existing data is overwritten when building the pool.',
        ),
    ),
)

__all__ = [
    'create',
]
