# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping XML config for objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Self

import click

from .command import Command
from .objects import is_object_mixin

if TYPE_CHECKING:
    from .state import State


class XMLCommand(Command):
    '''Class for commands that dump object XML.

       This provides the required callback and all needed parameters.'''
    def __init__(
        self: Self,
        name: str,
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        def cb(ctx: click.Context, state: State, entity: str, parent: str | None = None) -> None:
            with state.hypervisor as hv:
                if self.HAS_PARENT:
                    e = self.get_sub_entity(ctx, hv, parent, entity)
                else:
                    e = self.get_entity(ctx, hv, entity)

                xml = e.configRaw.rstrip().lstrip()

            click.echo(xml)

        if self.HAS_PARENT:
            header = dedent(f'''
            Dump the XML configuration for the specified { self.NAME }

            The { self.PARENT_METAVAR } argument should indicate which { self.PARENT_NAME } the { self.NAME } is in.''').lstrip()
        else:
            header = f'Dump the XML configuration for the specified { self.NAME }.'

        trailer = dedent('''
        This only operates on single { self.NAME }s.
        ''').lstrip()

        docstr = f'{ header }\n\n{ trailer }'

        params = self.mixin_params(required=True)

        super().__init__(
            name=name,
            help=docstr,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
