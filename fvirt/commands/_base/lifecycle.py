# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands object lifecycle commands.'''

from __future__ import annotations

import concurrent.futures

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self

import click

from .exitcode import ExitCode
from .match import MatchArgument, MatchCommand, get_match_or_entity
from .objects import is_object_mixin
from ...libvirt import InvalidOperation, LifecycleResult
from ...libvirt.runner import RunnerResult, run_entity_method, run_sub_entity_method

if TYPE_CHECKING:
    from .state import State
    from ...util.match import MatchAlias


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
            op_help: OperationHelpInfo,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        assert is_object_mixin(self)

        def cb(
            ctx: click.Context,
            state: State,
            match: MatchArgument | None,
            entity: str | None,
            parent: str | None = None,
            *args: Any,
            **kwargs: Any
        ) -> None:
            if op_help.idempotent_state:
                kwargs['idempotent'] = state.idempotent

            with state.hypervisor as hv:
                uri = hv.uri

                if parent is not None:
                    parent_obj = self.get_parent_obj(ctx, hv, parent)

                    futures = [state.pool.submit(
                        run_sub_entity_method,  # type: ignore
                        uri=uri,
                        hvprop=self.PARENT_ATTR,
                        parentprop=self.LOOKUP_ATTR,
                        method=method,
                        ident=(parent_obj.name, e.name),
                        arguments=args,
                        kwarguments=kwargs
                    ) for e in get_match_or_entity(
                        hv=hv,
                        obj=self,
                        match=match,
                        entity=entity,
                        ctx=ctx,
                        parent=parent_obj.name,
                    )]
                else:
                    futures = [state.pool.submit(
                        run_entity_method,  # type: ignore
                        uri=uri,
                        hvprop=self.LOOKUP_ATTR,
                        method=method,
                        ident=e.name,
                        arguments=args,
                        kwarguments=kwargs,
                    ) for e in get_match_or_entity(
                        hv=hv,
                        obj=self,
                        match=match,
                        entity=entity,
                        ctx=ctx,
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
                            ctx.fail(f'Unexpected internal error processing { self.NAME } "{ r.ident }".')
                        case RunnerResult(entity_found=False) as r:
                            click.echo(f'Could not find { self.NAME } "{ r.ident }".')
                            not_found += 1

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=False) as r:
                            click.echo(f'Unexpected error processing { self.NAME } "{ r.ident }".')

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=True, result=LifecycleResult.SUCCESS) as r:
                            click.echo(f'{ op_help.continuous.capitalize() } { self.NAME } "{ r.ident }".')
                            success += 1
                        case RunnerResult(method_success=True, result=LifecycleResult.NO_OPERATION) as r:
                            click.echo(f'{ self.NAME.capitalize() } "{ r.ident }" is already { op_help.idempotent_state }.')
                            skipped += 1

                            if state.idempotent:
                                success += 1
                        case RunnerResult(method_success=True, result=LifecycleResult.FAILURE) as r:
                            click.echo(f'Failed to { op_help.verb } { self.NAME } "{ r.ident }".')

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=True, result=LifecycleResult.TIMED_OUT) as r:
                            click.echo(f'Timed out waiting for { self.NAME } "{ r.ident }" to { op_help.verb }.')
                            timed_out += 1

                            if state.fail_fast:
                                break
                        case RunnerResult(method_success=True, result=LifecycleResult.FORCED) as r:
                            click.echo(f'{ self.NAME.capitalize() } "{ r.ident }" failed to { op_help.verb } and was forced to do so anyway.')
                            forced += 1
                        case _:
                            raise RuntimeError
                except InvalidOperation:
                    click.echo(f'Failed to { op_help.verb } { self.NAME } "{ r.ident }", operation is not supported for this { self.NAME }.')

                    if state.fail_fast:
                        break

                click.echo(f'Finished { op_help.continuous } specified { self.NAME }s.')
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
                    ctx.exit(ExitCode.FAILURE)

        params = tuple(params) + self.mixin_params(required=False)

        if self.HAS_PARENT:
            header = dedent(f'''
            { op_help.verb.capitalize() } one or more { self.NAME }s in the specified { self.PARENT_NAME }.

            The { self.PARENT_METAVAR } argument should indicate
            which { self.PARENT_NAME } to look for the { self.NAME }s
            in.''').lstrip()
        else:
            header = f'{ op_help.verb.capitalize() } one or more { self.NAME }s.'

        docstr = dedent(f'''
        { header }

        Either a specific { self.NAME } name to { op_help.verb } should
        be specified as NAME, or matching parameters should be specified
        using the --match option, which will then cause all active {
        self.NAME }s that match to be { op_help.past }.

        If more than one { self.NAME } is requested to be { op_help.past },
        a failure { op_help.continuous } any { self.NAME } will result
        in a non-zero exit code even if some { self.NAME }s were {
        op_help.past }.

        This command supports fvirt's fail-fast logic. In fail-fast
        mode, the first { self.NAME } that fails to be { op_help.past }
        will cause the operation to stop, and any failure will result
        in a non-zero exit code.''').lstrip()

        if op_help.idempotent_state:
            docstr += '\n\n' + dedent(f'''
            This command supports fvirt's idempotent logic. In idempotent
            mode, failing to { op_help.verb } a { self.NAME } because it
            is already { op_help.idempotent_state } will not be treated
            as an error.''').lstrip()
        else:
            docstr += '\n\n' + dedent('''
            This command does not support fvirt's idempotent logic. It
            will not behave any differently in idempotent mode than it
            does normally.''').lstrip()

        super().__init__(
            name=name,
            help=docstr,
            epilog=epilog,
            callback=cb,
            aliases=aliases,
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
