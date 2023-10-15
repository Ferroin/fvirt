# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command to print the local version information.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import click

from ._base.command import Command
from ..libvirt import API_VERSION
from ..version import VERSION

if TYPE_CHECKING:
    from ._base.state import State

HELP: Final = '''
Print version information for fvirt.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    click.echo(f'fvirt { VERSION }, using libvirt-python { API_VERSION }')


version: Final = Command(
    name='version',
    help=HELP,
    callback=cb,
)

__all__ = [
    'version',
]
