# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to print the configuration file search paths.'''

from __future__ import annotations

from typing import Final

import click

from .._base.command import Command
from .._base.config import CONFIG_PATHS
from .._base.exitcode import ExitCode
from .._base.state import State

HELP: Final = '''
Print the locations that will be searched for configuration files.

If a specific config file exists and would be used, it will be marked
in the output by a `*` at the end of the line.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    for path in CONFIG_PATHS:
        if str(path) == state.config.config_source:
            click.echo(f'{str(path)} *')
        else:
            click.echo(str(path))

    ctx.exit(ExitCode.SUCCESS)


paths: Final = Command(
    name='paths',
    help=HELP,
    callback=cb,
)

__all__ = [
    'paths',
]
