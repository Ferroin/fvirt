# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for creating new libvirt objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self, cast

import click

from .command import Command
from .exitcode import ExitCode
from .objects import is_object_mixin
from ...libvirt import Hypervisor, InvalidConfig
from ...libvirt.entity import Entity
from ...util.report import summary

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .state import State


def _read_file(path: str) -> tuple[str, str]:
    with click.open_file(path, mode='r') as f:
        return (cast(str, f.read()), path)


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

        def cb(
            ctx: click.Context,
            state: State,
            confpath: Sequence[str],
            parent: str | None = None,
            mode: str = 'define',
            **kwargs: Any,
        ) -> None:
            success = 0

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

            confdata = [_read_file(x) for x in confpath]

            with state.hypervisor as hv:
                if hv.read_only:
                    ctx.fail(f'Unable to create any { self.NAME }s, the hypervisor connection is read-only.')

                for conf in confdata:
                    if self.HAS_PARENT:
                        assert parent is not None

                        define_obj: Hypervisor | Entity = self.get_parent_obj(ctx, hv, parent)
                    else:
                        define_obj = hv

                for c, p in confdata:
                    try:
                        if NEW_PARAMS:
                            obj = getattr(define_obj, NEW_METHOD)(c, NEW_PARAMS)
                        else:
                            obj = getattr(define_obj, NEW_METHOD)(c)
                    except InvalidConfig:
                        click.echo(f'The configuration at { p } is not valid for a { self.NAME }.')

                        if state.fail_fast:
                            break
                    except Exception:
                        click.echo(f'Failed to create { self.NAME }.')

                        if state.fail_fast:
                            break
                    else:
                        click.echo(f'Successfully created { self.NAME }: "{ obj.name }".')
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

        trailer = dedent(f'''
        The CONFIGPATH argument should point to a valid XML configuration
        for a { self.NAME }. If more than one CONFIGPATH is specified, each
        should correspond to a separate { self.NAME } to be created.

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

        docstr = f'{ header }\n\n{ trailer }'

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
