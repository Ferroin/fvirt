# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that use object matching.'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, Self, Type, TypeVar

import click

from lxml import etree

from .command import Command
from ...libvirt.entity import Entity
from ...util.match import MatchAlias, MatchTarget

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, MutableMapping, Sequence

    from .state import State
    from ...libvirt import Hypervisor

P = ParamSpec('P')
T = TypeVar('T')

DEFAULT_MATCH = re.compile('.*')


def MatchTargetParam(aliases: Mapping[str, MatchAlias]) -> Type[click.ParamType]:
    '''Factory function for creating types for match tagets.

       This will produce a subclass of click.ParamType for parsing the
       first parameter that should be passed to the `--match` argument
       and converting it to a usable MatchTarget instance, based on the
       mapping of aliases.

       The resultant class can be used with the `type` argument for
       click.option decorators to properly parse match targets for the
       `--match` option.'''
    class MatchTargetParam(click.ParamType):
        name = 'match-target'

        def convert(self: Self, value: str | MatchTarget, param: Any, ctx: click.core.Context | None) -> MatchTarget:
            if isinstance(value, str):
                if value in aliases:
                    ret = MatchTarget(property=aliases[value].property)
                else:
                    ret = MatchTarget(xpath=etree.XPath(value, smart_strings=False))
            else:
                ret = value

            return ret

    return MatchTargetParam


class MatchPatternParam(click.ParamType):
    '''Class for processing match patterns.

       When used as a type for a Click option, this produces a re.Pattern
       object for use with the fvirt.util.match.matcher() function.'''
    name = 'pattern'

    def convert(self: Self, value: str | re.Pattern | None, param: Any, ctx: click.core.Context | None) -> re.Pattern:
        if isinstance(value, str):
            try:
                return re.compile(value)
            except re.error:
                self.fail(f'"{ value }" is not a valid pattern.', param, ctx)
        elif value is None:
            return DEFAULT_MATCH
        else:
            return value


def get_match_or_entity(
        *,
        hv: Hypervisor | Entity,
        hvprop: str,
        match: tuple[MatchTarget, re.Pattern] | None,
        entity: str | None,
        ctx: click.core.Context,
        doc_name: str,
        ) -> Sequence[Entity]:
    '''Get a list of entities based on the given parameters.

       This is a helper function intended to simplify writing callbacks for MatchCommands.'''
    entities: list[Entity] = []
    state: State = ctx.obj

    if match is not None:
        entities = list(getattr(hv, hvprop).match(match))

        if not entities and state.fail_if_no_match:
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
            callback: Callable[Concatenate[click.Context, State, P], T],
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
