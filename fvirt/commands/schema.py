# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command to dump fvirt's various schemas.'''

from __future__ import annotations

import json
import logging
import sys

from typing import TYPE_CHECKING, Final, cast

import click

from pydantic import BaseModel
from ruamel.yaml import YAML

from ._base.command import Command
from ._base.exitcode import ExitCode
from ..libvirt.models.domain import DomainInfo
from ..libvirt.models.storage_pool import PoolInfo
from ..libvirt.models.volume import VolumeInfo

if TYPE_CHECKING:
    from ._base.state import State

yaml: Final = YAML()
yaml.indent(sequence=4, offset=2)
yaml.default_flow_style = False

LOGGER: Final = logging.getLogger(__name__)
HELP: Final = '''
Display fvirt's schemas.

This command can be used to dump the schemas used by fvirt's object
templating in a variety of formats, allowing for easier validation using
external tools.

The schema to be displayed should be specified using the SCHEMA
argument. Specifying ‘list’ will list the recognized schemas instead
of displaying a specific schema.
'''.lstrip().rstrip()
MODEL_MAP: Final = {
    'domain': (
        'Schema for fvirt domain templates.',
        DomainInfo,
    ),
    'pool': (
        'Schema for fvirt storage pool templates.',
        PoolInfo,
    ),
    'volume': (
        'Schema for fvirt volume templates.',
        VolumeInfo,
    ),
}


def cb(
    ctx: click.Context,
    state: State,
    fmt: str,
    name: str,
) -> None:
    match name:
        case 'list':
            click.echo('The following schemas are recognized:')

            for k, v in MODEL_MAP.items():
                click.echo(f'  {k}: {v[0]}')

            ctx.exit(ExitCode.SUCCESS)
        case str() if name in MODEL_MAP.keys():
            schema = cast(BaseModel, MODEL_MAP[name][1]).model_json_schema()
        case _:
            LOGGER.error(f'Unrecognized schema "{name}". Use "fvirt schema list" to list known schemas.')
            ctx.exit(ExitCode.BAD_ARGUMENTS)

    match fmt:
        case 'json-compact':
            json.dump(schema, sys.stdout, sort_keys=True)
            ctx.exit(ExitCode.SUCCESS)
        case 'json':
            json.dump(schema, sys.stdout, indent=4, sort_keys=True)
            sys.stdout.write('\n')
            ctx.exit(ExitCode.SUCCESS)
        case 'yaml':
            yaml.dump(schema, sys.stdout)
            ctx.exit(ExitCode.SUCCESS)
        case _:
            raise RuntimeError


schema: Final = Command(
    name='schema',
    help=HELP,
    callback=cb,
    params=(
        click.Option(
            param_decls=('--format', 'fmt'),
            type=click.Choice((
                'json-compact',
                'json',
                'yaml',
            )),
            default='json',
            help='Specify the format to dump the schema in. Default is to dump it as JSON.',
        ),
        click.Argument(
            param_decls=('name',),
            nargs=1,
            required=True,
            metavar='SCHEMA',
        ),
    ),
)

__all__ = [
    'schema',
]
