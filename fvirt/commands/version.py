# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command to print the local version information.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ._base.command import Command

if TYPE_CHECKING:
    import click

    from ._base.state import State

HELP: Final = '''
Print version information for fvirt.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    import click

    from .. import VERSION
    from ..libvirt import API_VERSION

    click.echo(f'fvirt { VERSION }, using libvirt-python { API_VERSION }')


version: Final = Command(
    name='version',
    help=HELP,
    callback=cb,
)

__all__ = [
    'version',
]
