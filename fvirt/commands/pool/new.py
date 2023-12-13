# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create new storage pools.'''

from __future__ import annotations

from typing import Final, final

import click

from .._base.new import NewCommand
from .._base.objects import StoragePoolMixin


@final
class _NewPool(NewCommand, StoragePoolMixin):
    pass


new: Final = _NewPool(
    params=(
        click.Option(
            param_decls=('--build',),
            is_flag=True,
            default=False,
            help='Build the storage pool while creating it. Only supported with `--create`.',
        ),
        click.Option(
            param_decls=('--overwrite/--no-overwrite',),
            default=None,
            help='Control whether any existing data is overwritten when building the pool. Only supported with `--build`.',
        ),
    ),
    define_params=tuple(),
    create_params=(
        'build',
        'overwrite',
    ),
)

__all__ = [
    'new',
]
