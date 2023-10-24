# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Base class used for fvirt object creation commands.'''

from __future__ import annotations

import concurrent.futures

from abc import ABC, abstractmethod
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self, cast

import click

from .command import Command
from .exitcode import ExitCode
from .objects import ObjectMixin, is_object_mixin
from ...libvirt.exceptions import InvalidConfig
from ...libvirt.runner import RunnerResult, run_entity_method, run_hv_method

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

    from .state import State


def __read_file(path: str) -> str:
    with click.open_file(path, mode='r') as f:
        return cast(str, f.read())


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

            confdata = list(state.pool.map(__read_file, confpath))

            for cpath in confpath:
                with click.open_file(cpath, mode='r') as config:
                    confdata.append(config.read())

            uri = state.hypervisor.uri

            if state.hypervisor.read_only:
                ctx.fail(f'Unable to define { self.NAME }s, the hypervisor connection is read-only.')

            for conf in confdata:
                if self.HAS_PARENT:
                    assert parent is not None

                    futures = [state.pool.submit(
                        run_entity_method,  # type: ignore
                        uri=uri,
                        hvprop=self.PARENT_ATTR,
                        method=cast(NewCommand, self).NEW_METHOD,
                        ident=parent,
                        postproc=lambda x: x.name,
                        arguments=[c],
                        kwarguments=kwargs,
                    ) for c in confdata]
                else:
                    futures = [state.pool.submit(
                        run_hv_method,  # type: ignore
                        uri=uri,
                        method=cast(NewCommand, self).NEW_METHOD,
                        ident='',
                        postproc=lambda x: x.name,
                        arguments=[c],
                        kwarguments=kwargs,
                    ) for c in confdata]

            for f in concurrent.futures.as_completed(futures):
                match f.result():
                    case RunnerResult(attrs_found=False):
                        ctx.fail(f'Unexpected internal error defining new { self.NAME }.')
                    case RunnerResult(method_success=False, exception=InvalidConfig()):
                        click.echo(f'The configuration at { cpath } is not valid for a { self.NAME }.')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=False):
                        click.echo(f'Failed to create { self.NAME }.')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=True, postproc_success=False):
                        click.echo(f'Successfully defined { self.NAME }.')
                        success += 1
                    case RunnerResult(method_success=True, postproc_success=True, result=name):
                        click.echo(f'Successfully defined { self.NAME }: "{ name }".')
                        success += 1
                    case _:
                        raise RuntimeError

            click.echo(f'Finished defining specified { self.NAME }s.')
            click.echo('')
            click.echo('Results:')
            click.echo(f'  Success:     { success }')
            click.echo(f'  Failed:      { len(confdata) - success }')
            click.echo(f'Total:         { len(confdata) }')

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

        This command does not support fvirt's idempotent mode.''').lstrip()

        docstr = f'{ header }\n\n{ trailer }'

        params = tuple(params)

        if self.HAS_PARENT:
            params += self.mixin_parent_params()

        params += (click.Argument(
            param_decls=('configpath',),
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
