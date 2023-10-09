# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping XML config for objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Self, cast

import click

from .command import Command
from ...libvirt.entity import ConfigurableEntity

if TYPE_CHECKING:
    from .state import State


class XMLCommand(Command):
    '''Class for commands that dump object XML.

       This provides the required callback and all needed parameters.'''
    def __init__(
        self: Self,
        name: str,
        hvprop: str,
        metavar: str,
        doc_name: str,
        parent_prop: str | None = None,
        parent_name: str | None = None,
        parent_metavar: str | None = None,
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        parent_args = {parent_prop, parent_name, parent_metavar}

        if None in parent_args and parent_args != {None}:
            raise ValueError('Either all of parent_prop, parent_name, and parent_metavar must be specified, or neither must be specified.')

        def cb(ctx: click.Context, state: State, name: str, parent: str | None = None) -> None:
            with state.hypervisor as hv:
                if parent is None:
                    entity = cast(ConfigurableEntity, getattr(hv, hvprop).get(name))
                else:
                    assert parent_prop is not None

                    parent_obj = getattr(hv, hvprop).get(parent)

                    if parent_obj is None:
                        ctx.fail(f'Unable to find { parent_name } "{ parent }".')

                    entity = cast(ConfigurableEntity, getattr(parent, parent_prop).get(name))

                if entity is None:
                    ctx.fail(f'Unable to find { doc_name } "{ name }".')

                xml = entity.configRaw.rstrip().lstrip()

            click.echo(xml)

        if parent_prop is not None:
            header = dedent(f'''
            Dump the XML configuration for the specified { doc_name }

            The { parent_metavar } argument should indicate which { parent_name } the { doc_name } is in.''').lstrip()
        else:
            header = f'Dump the XML configuration for the specified { doc_name }.'

        trailer = dedent('''
        This only operates on single { doc_name }s.
        ''').lstrip()

        docstr = f'{ header }\n\n{ trailer }'

        params: tuple[click.Parameter, ...] = tuple()

        if parent_prop is not None:
            params += (click.Argument(
                param_decls=('parent',),
                nargs=1,
                required=True,
                metavar=parent_metavar,
            ),)

        params = (click.Argument(
            param_decls=('name',),
            nargs=1,
            required=True,
            metavar=metavar,
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
