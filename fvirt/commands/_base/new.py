# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Base class used for fvirt object creation commands.'''

from __future__ import annotations

from abc import ABC, abstractmethod
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self, cast

import click

from .command import Command
from .exitcode import ExitCode
from .objects import ObjectMixin, is_object_mixin
from ...libvirt import Hypervisor, InvalidConfig
from ...libvirt.entity import Entity
from ...util.report import summary

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .state import State


def _read_file(path: str) -> tuple[str, str]:
    with click.open_file(path, mode='r') as f:
        return (cast(str, f.read()), path)


class NewCommand(Command, ABC):
    '''A class for creating a libvirt object.

       This class takes care of the callback, options, and help text
       required for such commands.'''
    def __init__(
        self: Self,
        name: str,
        params: Sequence[click.Parameter] = [],
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
            **kwargs: Any,
        ) -> None:
            success = 0

            confdata = list(state.pool.map(_read_file, confpath))

            with state.hypervisor as hv:
                if hv.read_only:
                    ctx.fail(f'Unable to define { self.NAME }s, the hypervisor connection is read-only.')

                for conf in confdata:
                    if self.HAS_PARENT:
                        assert parent is not None

                        define_obj: Hypervisor | Entity = self.get_parent_obj(ctx, hv, parent)
                    else:
                        define_obj = hv

                for c, p in confdata:
                    try:
                        obj = getattr(define_obj, self.DEFINE_METHOD)(c, **kwargs)
                    except InvalidConfig:
                        click.echo(f'The configuration at { p } is not valid for a { self.NAME }.')

                        if state.fail_fast:
                            break
                    except Exception:
                        click.echo(f'Failed to create { self.NAME }.')

                        if state.fail_fast:
                            break
                    else:
                        click.echo(f'Successfully defined { self.NAME }: "{ obj.name }".')
                        success += 1

            click.echo(f'Finished defining specified { self.NAME }s.')
            click.echo('')
            click.echo(summary(
                total=len(confdata),
                success=success,
            ))

            if success != len(confdata) and confdata:
                ctx.exit(ExitCode.FAILURE)

        if self.HAS_PARENT:
            header = dedent(f'''
            Define one or more new { self.NAME }s in the specified { self.PARENT_NAME }.

            The { self.PARENT_METAVAR } argument should indicate
            which { self.PARENT_NAME } to create the { self.NAME }s
            in.''').lstrip()
        else:
            header = f'Define one or more new { self.NAME }s.'

        trailer = dedent(f'''
        The CONFIGPATH argument should point to a valid XML configuration
        for a { self.NAME }. If more than one CONFIGPATH is specified, each
        should correspond to a separate { self.NAME } to be defined.

        If a specified configuration describes a { self.NAME } that already
        exists, it will silently overwrite the the existing configuration
        for that { self.NAME }.

        All specified configuration files will be read before attempting
        to define any { self.NAME }s. Thus, if any configuration file is
        invalid, no { self.NAME }s will be defined.

        If more than one { self.NAME } is requested to be defined, a failure
        defining any { self.NAME } will result in a non-zero exit code even if
        some { self.NAME }s were defined.

        This command supports fvirt's fail-fast logic. In fail-fast mode, the
        first { self.NAME } that fails to be defined will cause the operation
        to stop, and any failure will result in a non-zero exit code.

        Configuration files will be read in parallel, but each { self.NAME
        } will be created one at a time without parallelization.

        This command does not support fvirt's idempotent mode.''').lstrip()

        docstr = f'{ header }\n\n{ trailer }'

        params = tuple(params)

        if self.HAS_PARENT:
            params += self.mixin_parent_params()

        params += (click.Argument(
            param_decls=('confpath',),
            type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
            nargs=-1,
        ),)

        super().__init__(
            name=name,
            help=docstr,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )

    @property
    @abstractmethod
    def NEW_METHOD(self: Self) -> str:
        '''The name of the method to be invoked to create the new object.'''
        return NotImplemented


class DefineCommand(NewCommand):
    '''Command class for defining new objects.'''
    @property
    def NEW_METHOD(self: Self) -> str:
        return cast(ObjectMixin, self).DEFINE_METHOD


class CreateCommand(NewCommand):
    '''Command class for creating new objects.'''
    @property
    def NEW_METHOD(self: Self) -> str:
        method = cast(ObjectMixin, self).CREATE_METHOD

        if method is None:
            raise RuntimeError

        return method
