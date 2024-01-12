# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the configuration.'''

from __future__ import annotations

import sys

from typing import Final

import click

from .._base.command import Command
from .._base.exitcode import ExitCode
from .._base.state import State

HELP: Final = '''
Dump the loaded configuration as a YAML document.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    from ruamel.yaml import YAML

    yaml: Final = YAML()
    yaml.indent(sequence=4, offset=2)
    yaml.default_flow_style = False
    yaml.representer.add_representer(type(None), lambda r, d: r.represent_scalar('tag:yaml.org,2002:null', 'null'))

    config = state.config.model_dump()

    yaml.dump(config, sys.stdout)
    ctx.exit(ExitCode.SUCCESS)


dump: Final = Command(
    name='dump',
    help=HELP,
    callback=cb,
)

__all__ = [
    'dump',
]
