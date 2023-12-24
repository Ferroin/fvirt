# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for creating new libvirt objects.'''

from __future__ import annotations

import logging
import sys

from textwrap import dedent
from typing import TYPE_CHECKING, Any, Final, Self

import click

from lxml import etree

from .command import Command
from .exitcode import ExitCode
from .objects import is_object_mixin
from ...libvirt import Hypervisor, InvalidConfig
from ...libvirt.entity import Entity
from ...templates import get_environment
from ...util.report import summary

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .state import State

HAVE_TEMPLATING: Final = get_environment() is not None
LOGGER: Final = logging.getLogger(__name__)

if HAVE_TEMPLATING:
    import json

    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.indent(sequence=4, offset=2)
    yaml.default_flow_style = False


def _read_xml_file(path: str) -> str:
    with click.open_file(path, mode='r') as f:
        return etree.tostring(etree.fromstring(f.read()), encoding='unicode')


def _read_json_file(path: str) -> Any:
    with click.open_file(path, mode='r') as f:
        return json.load(f)


def _read_yaml_file(path: str) -> Any:
    with click.open_file(path, mode='r') as f:
        return yaml.load(f)


class NewCommand(Command):
    '''Command to create or define libvirt objects.

       This class takes care of the callback, options, and help text
       required for such commands.'''
    def __init__(
        self: Self,
        params: Sequence[click.Parameter] = [],
        define_params: Sequence[str] = [],
        create_params: Sequence[str] = [],
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        use_templating = HAVE_TEMPLATING and self.CLASS._get_template_info() is not None

        def cb(
            ctx: click.Context,
            state: State,
            confpath: Sequence[str],
            parent: str | None = None,
            mode: str = 'define',
            template: str | None = None,
            template_schema: str | None = None,
            **kwargs: Any,
        ) -> None:
            assert is_object_mixin(self)

            success = 0

            if use_templating:
                info = self.CLASS._get_template_info()

                assert info is not None

                schema = info[0].model_json_schema()

                match template_schema:
                    case None:
                        pass
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

            match mode:
                case 'define':
                    NEW_METHOD = self.DEFINE_METHOD
                    NEW_PARAMS = {k: kwargs[k] for k in define_params}
                case 'create':
                    assert self.CREATE_METHOD is not None
                    NEW_METHOD = self.CREATE_METHOD
                    NEW_PARAMS = {k: kwargs[k] for k in create_params}
                case _:
                    raise RuntimeError

            match template:
                case 'json' | 'yaml':
                    match template:
                        case 'json':
                            pre_conf_data = [(_read_json_file(x), x) for x in confpath]
                        case 'yaml':
                            pre_conf_data = [(_read_yaml_file(x), x) for x in confpath]
                        case _:
                            raise RuntimeError

                    info = self.CLASS._get_template_info()

                    assert info is not None

                    model = info[0]

                    pre_conf_data2 = [(model.model_validate(x[0]), x[1]) for x in pre_conf_data]
                    confdata = [(self.CLASS.new_config(config=x[0]), x[1]) for x in pre_conf_data2]
                case None | 'none':
                    confdata = [(_read_xml_file(x), x) for x in confpath]
                case _:
                    raise RuntimeError

            with state.hypervisor as hv:
                if hv.read_only:
                    LOGGER.error(f'Unable to create any { self.NAME }s, the hypervisor connection is read-only.')
                    ctx.exit(ExitCode.OPERATION_FAILED)

                for conf in confdata:
                    if self.HAS_PARENT:
                        assert parent is not None

                        define_obj: Hypervisor | Entity = self.get_parent_obj(ctx, hv, parent)
                    else:
                        define_obj = hv

                for c, p in confdata:
                    try:
                        if NEW_PARAMS:
                            obj = getattr(define_obj, NEW_METHOD)(c, **NEW_PARAMS)
                        else:
                            obj = getattr(define_obj, NEW_METHOD)(c)
                    except InvalidConfig:
                        LOGGER.warning(f'The configuration at { p } is not valid for a { self.NAME }')

                        if state.fail_fast:
                            break
                    except Exception as e:
                        LOGGER.error(f'Failed to create { self.NAME }', exc_info=e)

                        if state.fail_fast:
                            break
                    else:
                        LOGGER.info(f'Successfully created { self.NAME }: "{ obj.name }".')
                        success += 1

            click.echo(f'Finished creatng specified { self.NAME }s.')
            click.echo('')
            click.echo(summary(
                total=len(confdata),
                success=success,
            ))

            if success != len(confdata) and confdata:
                ctx.exit(ExitCode.OPERATION_FAILED)

        if self.HAS_PARENT:
            header = dedent(f'''
            Create one or more new { self.NAME }s in the specified { self.PARENT_NAME }.

            The { self.PARENT_METAVAR } argument should indicate
            which { self.PARENT_NAME } to create the { self.NAME }s
            in.''').lstrip()
        else:
            header = f'Create one or more new { self.NAME }s.'

        mid = dedent(f'''
        The CONFIGPATH argument should point to a valid XML configuration
        for a { self.NAME }. If more than one CONFIGPATH is specified, each
        should correspond to a separate { self.NAME } to be created.
        ''')

        if use_templating:
            mid2 = dedent('''
            If the "--template" argument is specified, the CONFIGPATH
            argument should instead be a file of the specified format
            following the schema described by the output of the
            `--template-schema` argument.
            ''')

            mid = f'{mid}\n\n{mid2}'

        trailer = dedent(f'''
        If a specified configuration describes a { self.NAME } that already
        exists, it will silently overwrite the the existing configuration
        for that { self.NAME }.

        All specified configuration files will be read before attempting
        to create any { self.NAME }s. Thus, if any configuration file is
        invalid, no { self.NAME }s will be create.

        If more than one { self.NAME } is requested to be defined, a failure
        creating any { self.NAME } will result in a non-zero exit code even if
        some { self.NAME }s were created.

        This command supports fvirt's fail-fast logic. In fail-fast mode, the
        first { self.NAME } that fails to be created will cause the operation
        to stop, and any failure will result in a non-zero exit code.

        This command does not support fvirt's idempotent mode.''').lstrip()

        docstr = f'{header}\n\n{mid}\n\n{trailer}'

        params = tuple(params) + (
            click.Option(
                param_decls=('--define', 'mode'),
                flag_value='define',
                default=True,
                help=f'Define persistent {self.NAME}s. This is the default.',
            ),
        )

        if self.CREATE_METHOD is not None:
            params += (
                click.Option(
                    param_decls=('--create', 'mode'),
                    flag_value='create',
                    help=f'Create and start transient {self.NAME}s instead of defining persistent {self.NAME}s.',
                ),
            )

        if use_templating:
            params += (
                click.Option(
                    param_decls=('--template',),
                    type=click.Choice((
                        'none',
                        'json',
                        'yaml',
                    )),
                    default='none',
                    help=f'Prepare the {self.NAME} configuration from the specified type of template. "none" explicitly disables templating.',
                ),
                click.Option(
                    param_decls=('--template-schema',),
                    type=click.Choice((
                        'json-compact',
                        'json',
                        'yaml',
                    )),
                    default=None,
                    help=f'Dump the schema used when templating {self.NAME} configurations, using the specified format.',
                ),
            )

        if self.HAS_PARENT:
            params += self.mixin_parent_params()

        params += (
            click.Argument(
                param_decls=('confpath',),
                type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
                nargs=-1,
            ),
        )

        super().__init__(
            name='new',
            help=docstr,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
