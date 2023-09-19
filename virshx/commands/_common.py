# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Functions used in many commands.'''

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import click

from ..libvirt import Hypervisor, LifecycleResult

from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, matcher, print_match_help

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping, Sequence

    from ..libvirt.entity import RunnableEntity
    from ..util.match_alias import MatchAlias


def get_match_or_entity(
        *,
        hv: Hypervisor,
        hvprop: str,
        hvnameprop: str,
        match: tuple[MatchTarget, re.Pattern] | None,
        entity: str | None,
        ctx: click.core.Context,
        doc_name: str,
        ) -> Sequence[RunnableEntity]:
    '''Get a list of entities based on the given parameters.'''
    entities: list[RunnableEntity] = []

    if match is not None:
        select = matcher(*match)

        entities = cast(list[RunnableEntity], list(filter(select, getattr(hv, hvprop).__get__(hv))))

        if not entities and ctx.obj['fail_if_no_match']:
            click.echo(f'No { doc_name }s found matching the specified criteria.', err=True)
            ctx.exit(2)
    elif entity is not None:
        try:
            entities = cast(list[RunnableEntity], [getattr(hv, hvnameprop).__get__(hv)[entity]])
        except KeyError:
            click.echo(f'"{ entity }" is not a defined { doc_name } on this hypervisor.', err=True)
            ctx.exit(2)
    else:
        click.echo(f'Either match parameters or a { doc_name } name is required.', err=True)
        ctx.exit(1)

    return entities


def make_start_command(name: str, aliases: Mapping[str, MatchAlias], hvprop: str, hvnameprop: str, doc_name: str) -> click.Command:
    '''Produce a click Command to start a given type of libvirt entity.'''
    def cmd(
            ctx: click.core.Context,
            match: tuple[MatchTarget, re.Pattern] | None,
            match_help: bool,
            fail_if_no_match: bool,
            name: str | None,
            ) -> None:
        if match_help:
            print_match_help(aliases)
            ctx.exit(0)

        with Hypervisor(hvuri=ctx.obj['uri']) as hv:
            entities = get_match_or_entity(
                hv=hv,
                hvprop=hvprop,
                hvnameprop=hvnameprop,
                match=match,
                entity=name,
                ctx=ctx,
                doc_name=doc_name,
            )

            success = 0
            skipped = 0

            for e in entities:
                match e.start(idempotent=ctx.obj['idempotent']):
                    case LifecycleResult.SUCCESS:
                        click.echo(f'Started { doc_name } "{ e.name }".')
                        success += 1
                    case LifecycleResult.NO_OPERATION:
                        click.echo(f'Domain "{ e.name }" is already running.')

                        skipped += 1

                        if ctx.obj['idempotent']:
                            success += 1
                    case LifecycleResult.FAILURE:
                        click.echo(f'Failed to start { doc_name } "{ e.name }".')

                        if ctx.obj['fail_fast']:
                            break
                    case _:
                        raise RuntimeError

            if success or (not entities and not fail_if_no_match):
                click.echo(f'Successfully started { success } out of { len(entities) } { doc_name }s ({ skipped } already running).')

                if success != len(entities) and ctx.obj['fail_fast']:
                    ctx.exit(3)
            else:
                click.echo('Failed to start any { doc_name }s.')
                ctx.exit(3)

    cmd.__doc__ = f'''Start (previously defined) inactive { doc_name }s.

    Either a specific { doc_name } name to start should be specified as
    NAME, or matching parameters should be specified using the
    --match option, which will then cause all inactive { doc_name }s that
    match to be started.

    If more than one { doc_name } is requested to be started, a failure
    starting any { doc_name } will result in a non-zero exit code even if
    some { doc_name }s were started.

    This command supports virshx's fail-fast logic. In fail-fast mode,
    the first { doc_name } that fails to start will cause the operation to
    stop, and any failure will result in a non-zero exit code.

    This command supports virshx's idempotent logic. In idempotent
    mode, failing to start a { doc_name } because it is already running
    will not be treated as an error.'''

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.argument('name', nargs=1, required=False)(cmd)
    cmd = click.option('--match-help', is_flag=True, default=False,
                       help='Show help info about object matching.')(cmd)
    cmd = click.option('--match', type=(MatchTargetParam(aliases)(), MatchPatternParam()),
                       help='Limit { doc_name }s to operate on by match parameter. For more info, use `--match-help`')(cmd)
    cmd = click.command(name=name)(cmd)

    return cmd


def make_stop_command(name: str, aliases: Mapping[str, MatchAlias], hvprop: str, hvnameprop: str, doc_name: str) -> click.Command:
    '''Produce a click Command to stop (destroy) a given type of libvirt entity.'''
    def cmd(
            ctx: click.core.Context,
            match: tuple[MatchTarget, re.Pattern] | None,
            match_help: bool,
            fail_if_no_match: bool,
            name: str | None,
            ) -> None:
        if match_help:
            print_match_help(aliases)
            ctx.exit(0)

        with Hypervisor(hvuri=ctx.obj['uri']) as hv:
            entities = get_match_or_entity(
                hv=hv,
                hvprop=hvprop,
                hvnameprop=hvnameprop,
                match=match,
                entity=name,
                ctx=ctx,
                doc_name=doc_name,
            )

            success = 0
            skipped = 0

            for e in entities:
                match e.destroy(idempotent=ctx.obj['idempotent']):
                    case LifecycleResult.SUCCESS:
                        click.echo(f'Stopped { doc_name } "{ e.name }".')
                        success += 1
                    case LifecycleResult.NO_OPERATION:
                        click.echo(f'Domain "{ e.name }" is not running.')

                        skipped += 1

                        if ctx.obj['idempotent']:
                            success += 1
                    case LifecycleResult.FAILURE:
                        click.echo(f'Failed to stop { doc_name } "{ e.name }".')

                        if ctx.obj['fail_fast']:
                            break
                    case _:
                        raise RuntimeError

            if success or (not entities and not fail_if_no_match):
                click.echo(f'Successfully stopped { success } out of { len(entities) } { doc_name }s ({ skipped } not running).')

                if success != len(entities) and ctx.obj['fail_fast']:
                    ctx.exit(3)
            else:
                click.echo('Failed to stop any { doc_name }s.')
                ctx.exit(3)

    cmd.__doc__ = f'''Forcibly stop active { doc_name }s.

    Either a specific { doc_name } name to stop should be specified as
    NAME, or matching parameters should be specified using the
    --match option, which will then cause all active { doc_name }s that
    match to be stopped.

    If more than one { doc_name } is requested to be stopped, a failure
    stopping any { doc_name } will result in a non-zero exit code even if
    some { doc_name }s were stopped.

    This command supports virshx's fail-fast logic. In fail-fast mode,
    the first { doc_name } that fails to stop will cause the operation to
    stop, and any failure will result in a non-zero exit code.

    This command supports virshx's idempotent logic. In idempotent
    mode, failing to stop a { doc_name } because it is already stopped
    will not be treated as an error.'''

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.argument('name', nargs=1, required=False)(cmd)
    cmd = click.option('--match-help', is_flag=True, default=False,
                       help='Show help info about object matching.')(cmd)
    cmd = click.option('--match', type=(MatchTargetParam(aliases)(), MatchPatternParam()),
                       help='Limit { doc_name }s to operate on by match parameter. For more info, use `--match-help`')(cmd)
    cmd = click.command(name=name)(cmd)

    return cmd


__all__ = [
    'get_match_or_entity',
    'make_start_command',
    'make_stop_command',
]
