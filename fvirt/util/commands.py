# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Functions for constructing commands and preforming things commonly done in commands.'''

from __future__ import annotations

import functools

from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, ParamSpec, cast

import click
import libvirt

from lxml import etree

from ..libvirt import Hypervisor, InvalidConfig, InsufficientPrivileges
from ..libvirt.entity import Entity, ConfigurableEntity

from .match_params import MatchTargetParam, MatchPatternParam
from .tables import render_table, Column, ColumnsParam, print_columns, tabulate_entities

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping, Sequence, Callable

    from .match import MatchTarget, MatchAlias

    T = TypeVar('T')
    P = ParamSpec('P')


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
        entities = list(getattr(hv, hvprop).match(match))

        if not entities and ctx.obj['fail_if_no_match']:
            click.echo(f'No { doc_name }s found matching the specified criteria.', err=True)
            ctx.exit(2)
    elif entity is not None:
        item = getattr(hv, hvprop).get(entity)

        if item is None:
            click.echo(f'No { doc_name }s found with a name, UUID, or ID of "{ entity }" found.')
            ctx.exit(2)

        entities = [item]
    else:
        click.echo(f'Either match parameters or a { doc_name } name is required.', err=True)
        ctx.exit(1)

    return entities


def add_match_options(aliases: Mapping[str, MatchAlias], doc_name: str) -> \
        Callable[[Callable[P, T]], Callable[P, T]]:
    '''Produce a decorator that adds matching arguments to a function that will be turned into a Click command.'''
    def decorator(cmd: Callable[P, T]) -> Callable[P, T]:
        @click.option('--match', type=(MatchTargetParam(aliases)(), MatchPatternParam()),
                      help=f'Limit { doc_name }s to operate on by match parameter. For more info, see `fvirt help matching`')
        @functools.wraps(cmd)
        def inner(*args: P.args, **kwargs: P.kwargs) -> T:
            return cmd(*args, **kwargs)

        return inner

    return decorator


def make_help_command(group: click.Group, group_name: str, extra_topics: Mapping[str, tuple[str, str]]) -> click.Command:
    '''Produce a help command for the given group with the specified extra topics.

       The extra topics must be pre-formatted.'''
    def _print_topics(ctx: click.core.Context, cmds: Sequence[tuple[str, str]]) -> None:
        cmds_width = max([len(x[0]) for x in cmds]) + 2

        click.echo('')
        click.echo('Recognized subcommands:')
        for cmd in cmds:
            output = f'{ cmd[0] }{ " " * (cmds_width - len(cmd[0]) - 2) }  { cmd[1] }'
            click.echo(click.wrap_text(output, initial_indent='  ', subsequent_indent=(' ' * (cmds_width + 2))))

        topics_width = max([len(k) for k in extra_topics.keys()]) + 2

        click.echo('')
        click.echo('Additional help topics:')
        for topic in extra_topics:
            output = f'{ topic }{ " " * (topics_width - len(topic) - 2) }  { extra_topics[topic][0] }'
            click.echo(click.wrap_text(output, initial_indent='  ', subsequent_indent=(' ' * (topics_width + 2))))

    def cmd(ctx: click.Context, topic: str) -> None:
        cmds = {k: v.get_short_help_str() for k, v in group.commands.items()}

        match topic:
            case '':
                ctx.info_name = group_name
                click.echo(group.get_help(ctx))
                ctx.exit(0)
            case t if t in extra_topics:
                click.echo(extra_topics[t][1])
                ctx.exit(0)
            case t:
                subcmd = group.get_command(ctx, topic)

                if subcmd is None:
                    click.echo(f'{ topic } is not a recognized help topic.')
                    _print_topics(ctx, [(k, v) for k, v in cmds.items()])
                    ctx.exit(1)
                else:
                    ctx.info_name = topic
                    click.echo(subcmd.get_help(ctx))
                    if t == 'help':
                        _print_topics(ctx, [(k, v) for k, v in cmds.items()])
                    ctx.exit(0)

    cmd.__doc__ = f'''Print help for the { group_name } command.

    Without any arguments, prints the high-level help for the command itself.

    With an argument, prints help about that specific subcommand or topic.'''

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.argument('topic', default='')(cmd)
    cmd = click.command(name='help')(cmd)

    return cmd


def make_define_command(
        name: str,
        define_method: str,
        doc_name: str,
        parent: str | None = None,
        parent_name: str | None = None,
        parent_metavar: str | None = None,
        ) -> click.Command:
    '''Produce a click Command to define a given type of libvirt entity.'''
    parent_args = {parent, parent_name, parent_metavar}

    if None in parent_args and parent_args != {None}:
        raise ValueError('Either both of parent and parent_name must be specified, or neither must be specified.')

    def cmd(
            ctx: click.core.Context,
            confpath: Sequence[str],
            name: str | None = None,
            ) -> None:
        success = 0

        for cpath in confpath:
            with click.open_file(cpath, mode='r') as config:
                confdata = config.read()

            with Hypervisor(hvuri=ctx.obj['uri']) as hv:
                if parent is not None:
                    assert parent_name is not None
                    assert name is not None

                    define_object: Entity | Hypervisor = getattr(hv, parent).get(name)

                    if define_object is None:
                        ctx.fail(f'No { parent_name } with name, UUID, or ID of "{ name }" is defined on this hypervisor.')
                else:
                    define_object = hv

                try:
                    entity = getattr(define_object, define_method)(confdata)
                except InsufficientPrivileges:
                    ctx.fail(f'Specified hypervisor connection is read-only, unable to define { doc_name }')
                except InvalidConfig:
                    click.echo(f'The configuration at { cpath } is not valid for a { doc_name }.')

                    if ctx.obj['fail_fast']:
                        break

                click.echo(f'Successfully defined { doc_name }: { entity.name }')
                success += 1

        if success or (not confpath):
            click.echo(f'Successfully defineded { success } out of { len(confpath) } { doc_name }s.')

            if success != len(confpath):
                ctx.exit(3)
        else:
            click.echo('Failed to define any { doc_name }s.')
            ctx.exit(3)

    if parent is not None:
        header = f'''Define one or more new { doc_name }s in the specified { parent_name }.

        The { parent_metavar } argument should indicate which { parent_name } to create the { doc_name }s in.\n\n'''
    else:
        header = f'''Define one or more new { doc_name }s.\n\n'''

    trailer = f'''The CONFIGPATH argument should point to a valid XML configuration
    for a { doc_name }. If more than one CONFIGPATH is specified, each
    should correspond to a separate { doc_name } to be defined.

    If a specified configuration describes a { doc_name } that already
    exists, it will silently overwrite the the existing configuration
    for that { doc_name }.

    If more than one { doc_name } is requested to be defined, a failure
    defining any { doc_name } will result in a non-zero exit code even if
    some { doc_name }s were defined.

    This command supports fvirt's fail-fast logic. In fail-fast mode, the
    first { doc_name } that fails to be defined will cause the operation
    to stop, and any failure will result in a non-zero exit code.

    This command does not support fvirt's idempotent mode.'''

    cmd.__doc__ = f'{ header }{ trailer }'

    cmd = click.pass_context(cmd)  # type: ignore
    cmd = click.argument('configpath', nargs=-1)(cmd)
    if parent is not None:
        cmd = click.argument('name', metavar=parent_metavar, nargs=1, required=True)(cmd)
    cmd = click.command(name=name)(cmd)

    return cmd


__all__ = [
    'get_match_or_entity',
    'add_match_options',
    'make_help_command',
    'make_define_command',
]
