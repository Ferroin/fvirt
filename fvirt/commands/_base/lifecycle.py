# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands object lifecycle commands.'''

from __future__ import annotations

import concurrent.futures

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self, cast

import click

from .command import Command
from .match import MatchArgument, MatchCommand, get_match_or_entity
from ...libvirt import InvalidConfig, InvalidOperation, LifecycleResult
from ...libvirt.runner import RunnerResult, run_entity_method, run_hv_method, run_sub_entity_method

if TYPE_CHECKING:
    from .state import State
    from ...util.match import MatchAlias


def __read_file(path: str) -> str:
    with click.open_file(path, mode='r') as f:
        return cast(str, f.read())


@dataclass(kw_only=True, slots=True)
class OperationHelpInfo:
    '''Terms for templating into a lifecycle command help text.'''
    verb: str
    continuous: str
    past: str
    idempotent_state: str


class LifecycleCommand(MatchCommand):
    '''Class for object lifecycle commands.

       Unlike with a regular Command, the callback for a LifecycleCommand
       is expected to take a single object to operate on (as well as
       the click context and any additional parameters) and return an
       fvirt.libvirt.LifecycleResult object indicating the status of
       the operation.

       Construction of the list of objects to operate on, as well as
       failure handling and reporting of results, is handled entirely
       by the LifecycleCommand class itself.

       Note that there are no guarantees on the order in which entities
       will have the callback called on them, and multiple calls may be
       made in parallel, so the callback should be self-contained and
       thread-safe.

       This class auto-generates help text for the lifecycle command
       based on the info in op_help.'''
    def __init__(
            self: Self,
            name: str,
            method: str,
            aliases: Mapping[str, MatchAlias],
            doc_name: str,
            op_help: OperationHelpInfo,
            hvprop: str,
            parent: str | None = None,
            parent_name: str | None = None,
            parent_metavar: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        parent_args = {parent, parent_name, parent_metavar}

        if None in parent_args and parent_args != {None}:
            raise ValueError('Either all of parent, parent_name, and parent_metavar must be specified, or neither must be specified.')

        def cb(
            ctx: click.Context,
            state: State,
            match: MatchArgument | None,
            name: str | None,
            parent_obj: str | None = None,
            *args: Any,
            **kwargs: Any
        ) -> None:
            if op_help.idempotent_state:
                kwargs['idempotent'] = state.idempotent

            with state.hypervisor as hv:
                uri = hv.uri

                if parent_obj is not None:
                    assert parent is not None

                    parent_entity = getattr(hv, hvprop).get(parent_obj)

                    futures = [state.pool.submit(
                        run_sub_entity_method,
                        uri=uri,
                        hvprop=hvprop,
                        parentprop=parent,
                        method=method,
                        ident=(parent_entity.name, e.name),
                        arguments=args,
                        kwarguments=kwargs
                    ) for e in get_match_or_entity(
                        hv=parent_entity,
                        hvprop=parent,
                        match=match,
                        entity=name,
                        ctx=ctx,
                        doc_name=doc_name,
                    )]
                else:
                    futures = [state.pool.submit(
                        run_entity_method,  # type: ignore
                        uri=uri,
                        hvprop=hvprop,
                        method=method,
                        ident=e.name,
                        arguments=args,
                        kwarguments=kwargs,
                    ) for e in get_match_or_entity(
                        hv=hv,
                        hvprop=hvprop,
                        match=match,
                        entity=name,
                        ctx=ctx,
                        doc_name=doc_name,
                    )]

            success = 0
            skipped = 0
            timed_out = 0
            not_found = 0
            forced = 0

            for f in concurrent.futures.as_completed(futures):
                try:
                    match f.result():
                        case RunnerResult(attrs_found=False) as r:
                            ctx.fail(f'Unexpected internal error processing { doc_name } "{ r.ident }".')
                        case RunnerResult(entity_found=False) as r:
                            click.echo(f'Could not find { doc_name } "{ r.ident }".')
                            not_found += 1

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=False) as r:
                            click.echo(f'Unexpected error processing { doc_name } "{ r.ident }".')

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=True, result=LifecycleResult.SUCCESS) as r:
                            click.echo(f'{ op_help.continuous.capitalize() } { doc_name } "{ r.ident }".')
                            success += 1
                        case RunnerResult(method_success=True, result=LifecycleResult.NO_OPERATION) as r:
                            click.echo(f'{ doc_name.capitalize() } "{ r.ident }" is already { op_help.idempotent_state }.')
                            skipped += 1

                            if state.idempotent:
                                success += 1
                        case RunnerResult(method_success=True, result=LifecycleResult.FAILURE) as r:
                            click.echo(f'Failed to { op_help.verb } { doc_name } "{ r.ident }".')

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=True, result=LifecycleResult.TIMED_OUT) as r:
                            click.echo(f'Timed out waiting for { doc_name } "{ r.ident }" to { op_help.verb }.')
                            timed_out += 1

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=True, result=LifecycleResult.FORCED) as r:
                            click.echo(f'{ doc_name.capitalize() } "{ r.ident }" failed to { op_help.verb } and was forced to do so anyway.')
                            forced += 1
                        case _:
                            raise RuntimeError
                except InvalidOperation:
                    click.echo(f'Failed to { op_help.verb } { doc_name } "{ r.ident }", operation is not supported for this { doc_name }.')

                    if state.fail_fast:
                        break

                click.echo(f'Finished { op_help.continuous } specified { doc_name }s.')
                click.echo('')
                click.echo('Results:')
                click.echo(f'  Success:     { success }')
                click.echo(f'  Failed:      { len(futures) - success }')

                if skipped:
                    click.echo(f'    Skipped:   { skipped }')

                if timed_out:
                    click.echo(f'    Timed Out: { timed_out }')

                if forced:
                    click.echo(f'    Forced:    { forced }')

                click.echo(f'Total:         { len(futures) }')

                if success != len(futures) or (not futures and state.fail_if_no_match):
                    ctx.exit(3)

        params = tuple(params)

        if parent is not None:
            params += (click.Argument(
                param_decls=('parent_obj',),
                nargs=1,
                required=True,
                metavar=parent_metavar,
            ),)

        params += (click.Argument(
            param_decls=('name',),
            metavar=doc_name,
            nargs=1,
            required=False,
        ),)

        if parent is not None:
            header = dedent(f'''
            { op_help.verb.capitalize() } one or more { doc_name }s in the specified { parent_name }.

            The { parent_metavar } argument should indicate which {
            parent_name } to look for the { doc_name }s in.''').lstrip()
        else:
            header = f'{ op_help.verb.capitalize() } one or more { doc_name }s.'

        docstr = dedent(f'''
        { header }

        Either a specific { doc_name } name to { op_help.verb } should
        be specified as NAME, or matching parameters should be specified
        using the --match option, which will then cause all active {
        doc_name }s that match to be { op_help.past }.

        If more than one { doc_name } is requested to be { op_help.past },
        a failure { op_help.continuous } any { doc_name } will result
        in a non-zero exit code even if some { doc_name }s were {
        op_help.past }.

        This command supports fvirt's fail-fast logic. In fail-fast
        mode, the first { doc_name } that fails to be { op_help.past }
        will cause the operation to stop, and any failure will result
        in a non-zero exit code.''').lstrip()

        if op_help.idempotent_state:
            docstr += '\n\n' + dedent(f'''
            This command supports fvirt's idempotent
            logic. In idempotent mode, failing to { op_help.verb } a {
            doc_name } because it is already { op_help.idempotent_state }
            will not be treated as an error.''').lstrip()
        else:
            docstr += '\n\n' + dedent('''
            This command does not support fvirt's idempotent
            logic. It will not behave any differently in idempotent mode
            than it does normally.''').lstrip()

        super().__init__(
            name=name,
            help=docstr,
            epilog=epilog,
            callback=cb,
            aliases=aliases,
            doc_name=doc_name,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )


class SimpleLifecycleCommand(ABC, LifecycleCommand):
    '''Base class for trivial lifecycle commands.

       This handles the callback and operation info for a
       LifecycleCommand, but requires that the method on an entity not
       need any special handling other than being called with whatever
       arguments click would pass in based on the parameters.

       Subclasses must define METHOD and OP_HELP properties. The
       METHOD property should specify the name of the method to call on
       the entity in the callback, while the OP_HELP property should
       be an OperationHelpInfo instance for the command.'''
    def __init__(
            self: Self,
            name: str,
            aliases: Mapping[str, MatchAlias],
            doc_name: str,
            hvprop: str,
            parent: str | None = None,
            parent_name: str | None = None,
            parent_metavar: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        super().__init__(
            name=name,
            epilog=epilog,
            aliases=aliases,
            method=self.METHOD,
            hvprop=hvprop,
            parent=parent,
            parent_name=parent_name,
            parent_metavar=parent_metavar,
            doc_name=doc_name,
            op_help=self.OP_HELP,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )

    @property
    @abstractmethod
    def METHOD(self: Self) -> str:
        '''The name of the method that should be called on entities in the callback.'''

    @property
    @abstractmethod
    def OP_HELP(self: Self) -> OperationHelpInfo:
        '''An OperationHelpInfo instance for the class.'''


class StartCommand(SimpleLifecycleCommand):
    '''A class for starting a libvirt object.

       This class takes care of the callback and operation info for
       a LifecycleCommand.'''
    @property
    def METHOD(self: Self) -> str: return 'start'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='start',
            continuous='starting',
            past='started',
            idempotent_state='started',
        )


class StopCommand(SimpleLifecycleCommand):
    '''A class for stopping a libvirt object.

       This class takes care of the callback and operation info for
       a LifecycleCommand.'''
    @property
    def METHOD(self: Self) -> str: return 'destroy'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='stop',
            continuous='stopping',
            past='stopped',
            idempotent_state='stopped',
        )


class UndefineCommand(SimpleLifecycleCommand):
    '''A class for undefining a libvirt object.

       This class takes care of the callback and operation info for
       a LifecycleCommand.'''
    @property
    def METHOD(self: Self) -> str: return 'undefine'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='undefine',
            continuous='undefining',
            past='undefined',
            idempotent_state='undefined',
        )


class DefineCommand(Command):
    '''A class for defining a libvirt object.

       This class takes care of the callback, options, and help text
       required for such commands.'''
    def __init__(
            self: Self,
            name: str,
            doc_name: str,
            method: str,
            epilog: str | None = None,
            parent: str | None = None,
            parent_name: str | None = None,
            parent_metavar: str | None = None,
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        parent_args = {parent, parent_name, parent_metavar}

        if None in parent_args and parent_args != {None}:
            raise ValueError('Either all of parent, parent_name, and parent_metavar must be specified, or neither must be specified.')

        def cb(ctx: click.Context, state: State, confpath: Sequence[str], parent_obj: str | None = None) -> None:
            success = 0

            confdata = list(state.pool.map(__read_file, confpath))

            for cpath in confpath:
                with click.open_file(cpath, mode='r') as config:
                    confdata.append(config.read())

            uri = state.hypervisor.uri

            if state.hypervisor.read_only:
                ctx.fail(f'Unable to define { doc_name }s, the hypervisor connection is read-only.')

            for conf in confdata:
                if parent is not None:
                    assert parent_obj is not None

                    futures = [state.pool.submit(
                        run_entity_method,  # type: ignore
                        uri=uri,
                        hvprop=parent,
                        method=method,
                        ident=parent_obj,
                        postproc=lambda x: x.name,
                        arguments=[c],
                    ) for c in confdata]
                else:
                    futures = [state.pool.submit(
                        run_hv_method,  # type: ignore
                        uri=uri,
                        method=method,
                        ident='',
                        postproc=lambda x: x.name,
                        arguments=[c],
                    ) for c in confdata]

            for f in concurrent.futures.as_completed(futures):
                match f.result():
                    case RunnerResult(attrs_found=False):
                        ctx.fail(f'Unexpected internal error defining new { doc_name }.')
                    case RunnerResult(method_success=False, exception=InvalidConfig()):
                        click.echo(f'The configuration at { cpath } is not valid for a { doc_name }.')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=False):
                        click.echo(f'Failed to create { doc_name }.')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=True, postproc_success=False):
                        click.echo(f'Successfully defined { doc_name }.')
                        success += 1
                    case RunnerResult(method_success=True, postproc_success=True, result=name):
                        click.echo(f'Successfully defined { doc_name }: "{ name }".')
                        success += 1
                    case _:
                        raise RuntimeError

            click.echo(f'Finished defining specified { doc_name }s.')
            click.echo('')
            click.echo('Results:')
            click.echo(f'  Success:     { success }')
            click.echo(f'  Failed:      { len(confdata) - success }')
            click.echo(f'Total:         { len(confdata) }')

            if success != len(confdata) and confdata:
                ctx.exit(3)

        if parent is not None:
            header = dedent(f'''
            Define one or more new { doc_name }s in the specified { parent_name }.

            The { parent_metavar } argument should indicate which { parent_name } to create the { doc_name }s in.''').lstrip()
        else:
            header = f'Define one or more new { doc_name }s.'

        trailer = dedent(f'''
        The CONFIGPATH argument should point to a valid XML configuration
        for a { doc_name }. If more than one CONFIGPATH is specified, each
        should correspond to a separate { doc_name } to be defined.

        If a specified configuration describes a { doc_name } that already
        exists, it will silently overwrite the the existing configuration
        for that { doc_name }.

        All specified configuration files will be read before attempting
        to define any { doc_name }s. Thus, if any configuration file is
        invalid, no { doc_name }s will be defined.

        If more than one { doc_name } is requested to be defined, a failure
        defining any { doc_name } will result in a non-zero exit code even if
        some { doc_name }s were defined.

        This command supports fvirt's fail-fast logic. In fail-fast mode, the
        first { doc_name } that fails to be defined will cause the operation
        to stop, and any failure will result in a non-zero exit code.

        This command does not support fvirt's idempotent mode.''').lstrip()

        docstr = f'{ header }\n\n{ trailer }'

        params: tuple[click.Parameter, ...] = tuple()

        if parent is not None:
            params += (click.Argument(
                param_decls=('parent_obj',),
                nargs=1,
                required=True,
                metavar=parent_metavar,
            ),)

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
