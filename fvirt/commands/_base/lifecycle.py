# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands object lifecycle commands.'''

from __future__ import annotations

import functools
import re

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, Self, cast

import click

from .command import Command
from .match import MatchCommand, get_match_or_entity
from ...libvirt import Hypervisor, InsufficientPrivileges, InvalidConfig, LifecycleResult
from ...libvirt.entity import Entity, RunnableEntity
from ...util.match import MatchTarget

if TYPE_CHECKING:
    from ...util.match import MatchAlias

P = ParamSpec('P')


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
            callback: Callable[Concatenate[click.Context, Entity, P], LifecycleResult],
            aliases: Mapping[str, MatchAlias],
            doc_name: str,
            op_help: OperationHelpInfo,
            hvprop: str,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            context_settings: MutableMapping[str, Any] = dict(),
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        @functools.wraps(callback)
        def cb(ctx: click.Context, *args: P.args, **kwargs: P.kwargs) -> None:
            with Hypervisor(hvuri=ctx.obj['uri']) as hv:
                entities = cast(Sequence[RunnableEntity], get_match_or_entity(
                    hv=hv,
                    hvprop=hvprop,
                    match=cast(tuple[MatchTarget, re.Pattern], kwargs.get('match')),
                    entity=name,
                    ctx=ctx,
                    doc_name=doc_name,
                ))

                success = 0
                skipped = 0
                timed_out = 0
                forced = 0

                for e in entities:
                    match callback(ctx, e, *args, **kwargs):
                        case LifecycleResult.SUCCESS:
                            click.echo(f'{ op_help.continuous.capitalize() } { doc_name } "{ e.name }".')
                            success += 1
                        case LifecycleResult.NO_OPERATION:
                            click.echo(f'{ doc_name.capitalize() } "{ e.name }" is already { op_help.idempotent_state }.')
                            skipped += 1

                            if ctx.obj['idempotent']:
                                success += 1
                        case LifecycleResult.FAILURE:
                            click.echo(f'Failed to { op_help.verb } { doc_name } "{ e.name }".')

                            if ctx.obj['fail_fast']:
                                break
                        case LifecycleResult.TIMED_OUT:
                            click.echo(f'Timed out waiting for { doc_name } "{ e.name }" to { op_help.verb }.')
                            timed_out += 1

                            if ctx.obj['fail_fast']:
                                break
                        case LifecycleResult.FORCED:
                            click.echo(f'{ doc_name.capitalize() } "{ e.name }" failed to { op_help.verb } and was forced to do so anyway.')
                            forced += 1
                        case _:
                            raise RuntimeError

                click.echo(f'Finished { op_help.continuous } specified { doc_name }s.')
                click.echo('')
                click.echo('Results:')
                click.echo(f'  Success:     { success }')
                click.echo(f'  Failed:      { len(entities) - success }')

                if skipped:
                    click.echo(f'    Skipped:   { skipped }')

                if timed_out:
                    click.echo(f'    Timed Out: { timed_out }')

                if forced:
                    click.echo(f'    Forced:    { forced }')

                click.echo(f'Total:         { len(entities) }')

                if success != len(entities) and ctx.obj['fail_fast'] or (not entities and ctx.obj['fail_if_no_match']):
                    ctx.exit(3)

        params = tuple(params) + (click.Argument(
            param_decls=('name',),
            metavar=doc_name,
            nargs=1,
            required=False,
        ),)

        docstr = dedent(f'''
        { op_help.verb.capitalize() } one or more { doc_name }s.

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
            context_settings=context_settings,
            hidden=hidden,
            deprecated=deprecated,
        )


class SimpleLifecycleCommand(ABC, LifecycleCommand):
    '''Base class for trivial lifecycle commands.

       This handles the callback and operation info for a
       LifecycleCommand, but requires that the method on an entity
       not need any special handling other than being called with no
       arguments.

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
            epilog: str | None = None,
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        def cb(ctx: click.Context, entity: Entity, /) -> LifecycleResult:
            return cast(LifecycleResult, getattr(entity, self.METHOD)(idempotent=ctx.obj['idempotent']))

        super().__init__(
            name=name,
            epilog=epilog,
            callback=cb,
            aliases=aliases,
            hvprop=hvprop,
            doc_name=doc_name,
            op_help=self.OP_HELP,
            params=tuple(),
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
            raise ValueError('Either both of parent and parent_name must be specified, or neither must be specified.')

        def cb(ctx: click.Context, confpath: Sequence[str], parent_obj: str | None = None) -> None:
            success = 0

            confdata = []

            for cpath in confpath:
                with click.open_file(cpath, mode='r') as config:
                    confdata.append(config.read())

            with Hypervisor(hvuri=ctx.obj['uri']) as hv:
                if parent is not None:
                    assert parent_name is not None
                    assert name is not None

                    define_object: Entity | Hypervisor = getattr(hv, parent).get(name)

                    if define_object is None:
                        ctx.fail(f'No { parent_name } with name, UUID, or ID of "{ name }" is defined on this hypervisor.')
                else:
                    define_object = hv

                for conf in confdata:
                    try:
                        entity = getattr(define_object, method)(confdata)
                    except InsufficientPrivileges:
                        ctx.fail(f'Specified hypervisor connection is read-only, unable to define { doc_name }')
                    except InvalidConfig:
                        click.echo(f'The configuration at { cpath } is not valid for a { doc_name }.')

                        if ctx.obj['fail_fast']:
                            break

                    click.echo(f'Successfully defined { doc_name }: { entity.name }')
                    success += 1

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
                param_decls=('name',),
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
