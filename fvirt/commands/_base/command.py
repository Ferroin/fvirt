# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for other fvirt commands.'''

from __future__ import annotations

import functools

from typing import TYPE_CHECKING, Concatenate, ParamSpec, Self, TypeVar

import click

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .state import State

P = ParamSpec('P')
T = TypeVar('T')


class Command(click.Command):
    '''Base class used for all commands in fvirt.

       This doesn’t really do much other than ensuring that contexts
       get passed along to the command callbacks, setting a few
       defaults for the initializer, and making the init signature a
       bit stricter.'''
    def __init__(
            self: Self,
            name: str,
            help: str,
            callback: Callable[Concatenate[click.Context, State, P], T],
            short_help: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        if short_help is None:
            short_help = help.splitlines()[0]

        @functools.wraps(callback)
        def f(*args: P.args, **kwargs: P.kwargs) -> T:
            ctx = click.get_current_context()
            return callback(ctx, ctx.obj, *args, **kwargs)

        super().__init__(
            name=name,
            help=help,
            epilog=epilog,
            short_help=short_help,
            callback=f,
            params=list(params),
            add_help_option=True,
            no_args_is_help=False,
            hidden=hidden,
            deprecated=deprecated,
        )


__all__ = [
    'Command',
]
