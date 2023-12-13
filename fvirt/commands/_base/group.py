# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Base class used for fvirt command groups.'''

from __future__ import annotations

import functools
import importlib

from typing import TYPE_CHECKING, Concatenate, ParamSpec, Self, TypeVar, cast

import click

from .help import AliasHelpTopic, HelpCommand, HelpTopic

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from ...util.match import MatchAlias

P = ParamSpec('P')
T = TypeVar('T')


class Group(click.Group):
    '''Base class used for all commands in fvirt.

       This does most of the same things that
       fvirt.commands._base.command.Command does, as well as adding a help
       command automatically and handling lazy-loading of commands.'''
    def __init__(
            self: Self,
            name: str,
            help: str,
            callback: Callable[Concatenate[click.Context, P], T],
            commands: Sequence[click.Command] = [],
            lazy_commands: Mapping[str, str] = dict(),
            help_topics: Iterable[HelpTopic] = [],
            aliases: Mapping[str, MatchAlias] = dict(),
            doc_name: str | None = None,
            short_help: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        self.__lazy_commands = lazy_commands

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

    def list_commands(self: Self, ctx: click.Context) -> list[str]:
        base = super().list_commands(ctx)
        lazy = sorted(self.__lazy_commands.keys())
        return base + lazy

    def get_command(self: Self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self.__lazy_commands:
            return cast(click.Command, self._lazy_load(name))

        return super().get_command(ctx, name)

    @property
    def lazy_commands(self: Self) -> Mapping[str, str]:
        '''A mapping of the lazy-loaded commands for this group.'''
        return self.__lazy_commands

    @functools.cache
    def _lazy_load(self: Self, cmd_name: str) -> click.BaseCommand:
        import_path = self.__lazy_commands[cmd_name]
        modname, cmd_name = import_path.rsplit('.', 1)
        mod = importlib.import_module(modname)
        cmd = getattr(mod, cmd_name)

        if not isinstance(cmd, click.BaseCommand):
            raise ValueError(
                f'Lazy loading of { import_path } failed by returning '
                'a non-command object'
            )

        return cmd


__all__ = [
    'Group',
]
