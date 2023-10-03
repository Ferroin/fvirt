# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt command groups.'''

from __future__ import annotations

import functools

from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, Self, TypeVar

import click

from .help import AliasHelpTopic, HelpCommand, HelpTopic

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence

    from ...util.match import MatchAlias


P = ParamSpec('P')
T = TypeVar('T')


class Group(click.Group):
    '''Base class used for all commands in fvirt.

       This does most of the same things that
       fvirt.commands._base.command.Command does, as well as adding a
       help command automatically.'''
    def __init__(
            self: Self,
            name: str,
            help: str,
            callback: Callable[Concatenate[click.core.Context, P], T],
            commands: Sequence[click.Command] = [],
            help_topics: Iterable[HelpTopic] = [],
            aliases: Mapping[str, MatchAlias] = dict(),
            doc_name: str | None = None,
            short_help: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            context_settings: MutableMapping[str, Any] = dict(),
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        if short_help is None:
            short_help = help.splitlines()[0]

        if doc_name is None:
            doc_name = name

        @functools.wraps(callback)
        def f(*args: P.args, **kwargs: P.kwargs) -> T:
            return callback(click.get_current_context(), *args, **kwargs)

        super().__init__(
            name=name,
            help=help,
            epilog=epilog,
            short_help=short_help,
            callback=f,
            params=list(params),
            context_settings=context_settings,
            commands=commands,
            add_help_option=True,
            no_args_is_help=False,
            hidden=hidden,
            deprecated=deprecated,
        )

        self.name = name

        help_topics = tuple(help_topics)

        if aliases:
            help_topics = help_topics + (AliasHelpTopic(
                aliases=aliases,
                group_name=self.name,
                doc_name=doc_name,
            ),)

        self.add_command(HelpCommand(
            group=self,
            topics=help_topics,
        ))


__all__ = [
    'Group',
]
