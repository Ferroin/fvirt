# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for an object.'''

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self

import click

from .command import Command

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .state import State


@dataclass(kw_only=True, slots=True)
class InfoItem:
    '''Represent an item to be printed by an InfoCommand.'''
    name: str
    prop: str
    color: Callable[[Any], str] = lambda x: str(x)


class InfoCommand(Command):
    '''Class for commands that prints detailed info about an object.

       This completely encapsulates the callback and all the other
       required info.'''
    def __init__(
        self: Self,
        name: str,
        info_items: Sequence[InfoItem],
        hvprop: str,
        doc_name: str,
        parent: str | None = None,
        parent_name: str | None = None,
        parent_metavar: str | None = None,
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        parent_args = {parent, parent_name, parent_metavar}

        if None in parent_args and parent_args != {None}:
            raise ValueError('Either all of parent, parent_name, and parent_metavar must be specified, or neither must be specified.')

        def cb(
            ctx: click.Context,
            state: State,
            name: str,
            parent_obj: str | None = None,
        ) -> None:
            output = f'{ doc_name.capitalize() }: { name }\n'

            with state.hypervisor as hv:
                if parent_obj is not None:
                    assert parent is not None
                    assert parent_name is not None

                    parent_entity = getattr(hv, hvprop).get(parent_obj)

                    if parent_entity is None:
                        click.echo(f'Could not find { parent_name } "{ parent_obj }".')
                        ctx.exit(2)

                    entity = getattr(parent_entity, parent).get(name)
                    output += f'  { parent_name.capitalize() }: { parent_obj }\n'
                else:
                    entity = getattr(hv, hvprop).get(name)

                if entity is None:
                    click.echo(f'Could not find { doc_name } "{ name }".')
                    ctx.exit(2)

                for item in info_items:
                    value = item.color(getattr(entity, item.prop, None))

                    if value is not None:
                        output += f'  { item.name }: { value }\n'

            click.echo(output.rstrip())

        params: tuple[click.Parameter, ...] = tuple()

        if parent is not None:
            params += (click.Argument(
                param_decls=('parent_obj',),
                nargs=1,
                required=True,
                metavar=parent_metavar,
            ),)
            header = dedent(f'''
            Show detailed information about a { doc_name }.

            The { parent_metavar } argument should specify which {
            parent_name } to look for the { doc_name } in.
            ''').lstrip().rstrip()
        else:
            header = f'Show detailed information about a { doc_name }.'

        params += (click.Argument(
            param_decls=('name',),
            metavar=doc_name,
            nargs=1,
            required=False,
        ),)

        docstr = header + '\n\n' + dedent(f'''
        A specific { doc_name } should be specified to retrieve
        information about.
        ''')

        super().__init__(
            name=name,
            help=docstr,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
