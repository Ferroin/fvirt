# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Functions used in many commands.'''

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click
import libvirt

from lxml import etree

from ..libvirt import Hypervisor, LifecycleResult
from ..libvirt.entity import Entity, RunnableEntity, ConfigurableEntity

from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, matcher, print_match_help
from ..util.tables import render_table, Column, ColumnsParam, print_columns, tabulate_entities

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping, Sequence

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
        ) -> Sequence[Entity]:
    '''Get a list of entities based on the given parameters.'''
    entities: list[Entity] = []

    if match is not None:
        select = matcher(*match)

        entities = cast(list[Entity], list(filter(select, getattr(hv, hvprop))))

        if not entities and ctx.obj['fail_if_no_match']:
            click.echo(f'No { doc_name }s found matching the specified criteria.', err=True)
            ctx.exit(2)
    elif entity is not None:
        try:
            entities = cast(list[Entity], [getattr(hv, hvnameprop)[entity]])
        except KeyError:
            click.echo(f'"{ entity }" is not a defined { doc_name } on this hypervisor.', err=True)
            ctx.exit(2)
    else:
        click.echo(f'Either match parameters or a { doc_name } name is required.', err=True)
        ctx.exit(1)

    return entities


def make_list_command(
        name: str,
        aliases: Mapping[str, MatchAlias],
        columns: Mapping[str, Column],
        default_cols: Sequence[str],
        hvprop: str,
        doc_name: str,
        ) -> click.Command:
    '''Produce a click Command to list a given type of libvirt entity.'''
    def cmd(
            ctx: click.core.Context,
            cols: list[str],
            match: tuple[MatchTarget, re.Pattern] | None,
            match_help: bool,
            ) -> None:
        if cols == ['list']:
            print_columns(columns, default_cols)
            ctx.exit(0)

        if match_help:
            print_match_help(aliases)
            ctx.exit(0)

        if match is not None:
            select = matcher(*match)
        else:
            def select(x: Any) -> bool: return True

        with Hypervisor(hvuri=ctx.obj['uri']) as hv:
            entities = cast(list[Entity], list(filter(select, getattr(hv, hvprop))))

            if not entities and ctx.obj['fail_if_no_match']:
                ctx.fail(f'No { doc_name }s found matching the specified parameters.')

            data = tabulate_entities(entities, columns, cols)

        output = render_table(
            data,
            [columns[x] for x in cols],
        )

        click.echo(output)

    cmd.__doc__ = f'''List { doc_name }s.

    This will produce a (reasonably) nicely formatted table of { doc_name }s,
    possibly limited by the specified matching parameters.'''

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.option('--match-help', is_flag=True, default=False,
                       help='Show help info about object matching.')(cmd)
    cmd = click.option('--match', type=(MatchTargetParam(aliases)(), MatchPatternParam()),
                       help='Limit { doc_name }s to operate on by match parameter. For more info, use `--match-help`')(cmd)
    cmd = click.option('--columns', 'cols', type=ColumnsParam(columns, f'{ doc_name } columns')(), nargs=1,
                       help=f'A comma separated list of columns to show when listing { doc_name }s. ' +
                            'Use `--columns list` to list recognized column names.',
                       default=default_cols)(cmd)
    cmd = click.command(name=name)(cmd)

    return cmd


def make_sub_list_command(
        name: str,
        aliases: Mapping[str, MatchAlias],
        columns: Mapping[str, Column],
        default_cols: Sequence[str],
        hvprop: str,
        objprop: str,
        doc_name: str,
        obj_doc_name: str,
        ) -> click.Command:
    '''Produce a click Command to list a given type of libvirt entity.'''
    def cmd(
            ctx: click.core.Context,
            cols: list[str],
            match: tuple[MatchTarget, re.Pattern] | None,
            match_help: bool,
            name: str,
            ) -> None:
        if cols == ['list']:
            print_columns(columns, default_cols)
            ctx.exit(0)

        if match_help:
            print_match_help(aliases)
            ctx.exit(0)

        if match is not None:
            select = matcher(*match)
        else:
            def select(x: Any) -> bool: return True

        with Hypervisor(hvuri=ctx.obj['uri']) as hv:
            try:
                obj = getattr(hv, hvprop)[name]
            except KeyError:
                ctx.fail(f'No { obj_doc_name } with name "{ name }" is defined on this hypervisor.')

            entities = filter(select, getattr(obj, objprop))

            if not entities and ctx.obj['fail_if_no_match']:
                ctx.fail('No { doc_name }s found matching the specified parameters.')

            data = tabulate_entities(entities, columns, cols)

        output = render_table(
            data,
            [columns[x] for x in cols],
        )

        click.echo(output)

    cmd.__doc__ = f'''List { doc_name }s in a given { obj_doc_name }.

    This will produce a (reasonably) nicely formatted table of { doc_name
    }s in the { obj_doc_name } specified by NAME, possibly limited by
    the specified matching parameters.'''

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.argument('name', nargs=1, required=True)(cmd)
    cmd = click.option('--match-help', is_flag=True, default=False,
                       help='Show help info about object matching.')(cmd)
    cmd = click.option('--match', type=(MatchTargetParam(aliases)(), MatchPatternParam()),
                       help='Limit { doc_name }s to operate on by match parameter. For more info, use `--match-help`')(cmd)
    cmd = click.option('--columns', 'cols', type=ColumnsParam(columns, f'{ doc_name } columns')(), nargs=1,
                       help=f'A comma separated list of columns to show when listing { doc_name }s. ' +
                            'Use `--columns list` to list recognized column names.',
                       default=default_cols)(cmd)
    cmd = click.command(name=name)(cmd)

    return cmd


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
            entities = cast(Sequence[RunnableEntity], get_match_or_entity(
                hv=hv,
                hvprop=hvprop,
                hvnameprop=hvnameprop,
                match=match,
                entity=name,
                ctx=ctx,
                doc_name=doc_name,
            ))

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
            entities = cast(Sequence[RunnableEntity], get_match_or_entity(
                hv=hv,
                hvprop=hvprop,
                hvnameprop=hvnameprop,
                match=match,
                entity=name,
                ctx=ctx,
                doc_name=doc_name,
            ))

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


def make_xslt_command(name: str, aliases: Mapping[str, MatchAlias], hvprop: str, hvnameprop: str, doc_name: str) -> click.Command:
    '''Produce a click Command to modify a given type of libvirt entity with an XSLT document.'''
    def cmd(
            ctx: click.core.Context,
            match: tuple[MatchTarget, re.Pattern] | None,
            match_help: bool,
            xslt: Path,
            name: str | None,
            ) -> None:
        if match_help:
            print_match_help(aliases)
            ctx.exit(0)

        xform = etree.XSLT(etree.parse(xslt))

        with Hypervisor(hvuri=ctx.obj['uri']) as hv:
            entities = cast(Sequence[ConfigurableEntity], get_match_or_entity(
                hv=hv,
                hvprop=hvprop,
                hvnameprop=hvnameprop,
                match=match,
                entity=name,
                ctx=ctx,
                doc_name=doc_name,
            ))

            success = 0

            for e in entities:
                try:
                    e.applyXSLT(xform)
                except libvirt.libvirtError:
                    click.echo(f'Failed to modify { doc_name } "{ e.name }".')

                    if ctx.obj['fail_fast']:
                        break
                else:
                    click.echo(f'Successfully modified { doc_name } "{ e.name }".')
                    success += 1

            if success or (not entities and not ctx.obj['fail_if_no_match']):
                click.echo(f'Successfully modified { success } out of { len(entities) } { doc_name }s.')

                if success != len(entities) and ctx.obj['fail_fast']:
                    ctx.exit(3)
            else:
                click.echo(f'Failed to modified any { doc_name }s.')
                ctx.exit(3)

    cmd.__doc__ = f'''Apply an XSLT document to one or more { doc_name }s.

    XSLT must be a path to a valid XSLT document. It must specify an
    output element, and the output element must specify an encoding
    of UTF-8. Note that xsl:strip-space directives may cause issues
    in the XSLT processor.

    Either a specific { doc_name } name to modify should be specified as
    NAME, or matching parameters should be specified using the --match
    option, which will then cause all matching { doc_name }s to be modified.

    This command supports virshx's fail-fast logic. In fail-fast mode,
    the first { doc_name } which the XSLT document fails to apply to will
    cause the operation to stop, and any failure will result in a
    non-zero exit code.

    This command does not support virshx's idempotent mode. It's
    behavior will not change regardless of whether idempotent mode
    is enabled or not.'''

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.argument('name', nargs=1, required=False)(cmd)
    cmd = click.argument('xslt', nargs=1, required=True,
                         type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True))(cmd)
    cmd = click.option('--match-help', is_flag=True, default=False,
                       help='Show help info about object matching.')(cmd)
    cmd = click.option('--match', type=(MatchTargetParam(aliases)(), MatchPatternParam()),
                       help='Limit { doc_name }s to operate on by match parameter. For more info, use `--match-help`')(cmd)
    cmd = click.command(name=name)(cmd)

    return cmd


__all__ = [
    'get_match_or_entity',
    'make_list_command',
    'make_sub_list_command',
    'make_start_command',
    'make_stop_command',
    'make_xslt_command',
]
