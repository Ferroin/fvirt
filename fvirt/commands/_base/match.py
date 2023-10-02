# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that use object matching.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Self, Any, ParamSpec, TypeVar, Concatenate

import click

from .command import Command

from ...libvirt.entity import Entity
from ...util.match import MatchAlias, MatchTarget
from ...util.match_params import MatchTargetParam, MatchPatternParam

if TYPE_CHECKING:
    import re

    from collections.abc import MutableMapping, Sequence, Callable, Mapping

    from ...libvirt import Hypervisor

P = ParamSpec('P')
T = TypeVar('T')


def get_match_or_entity(
        *,
        hv: Hypervisor,
        hvprop: str,
        match: tuple[MatchTarget, re.Pattern] | None,
        entity: str | None,
        ctx: click.core.Context,
        doc_name: str,
        ) -> Sequence[Entity]:
    '''Get a list of entities based on the given parameters.

       This is a helper function intended to simplify writing callbacks for MatchCommands.'''
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


class MatchCommand(Command):
    '''Class for commands that use matching arguments.'''
    def __init__(
            self: Self,
            name: str,
            help: str,
            callback: Callable[Concatenate[click.Context, P], T],
            aliases: Mapping[str, MatchAlias],
            doc_name: str,
            short_help: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            context_settings: MutableMapping[str, Any] = dict(),
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        params = tuple(params) + (click.Option(
            param_decls=('--match',),
            type=(MatchTargetParam(aliases)(), MatchPatternParam()),
            nargs=2,
            help=f'Limit { doc_name }s to operate on by match parameter. For more info, see `fvirt help matching`',
            default=None,
        ),)

        super().__init__(
            name=name,
            help=help,
            epilog=epilog,
            short_help=short_help,
            callback=callback,
            params=params,
            context_settings=context_settings,
            hidden=hidden,
            deprecated=deprecated,
        )


__all__ = [
    'MatchCommand',
]
