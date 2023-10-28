# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that list objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Self

import click

from .exitcode import ExitCode
from .match import MatchCommand
from .objects import is_object_mixin
from ...util.match import MatchAlias, MatchTarget
from ...util.tables import Column, ColumnsParam, column_info, render_table, tabulate_entities

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping, Sequence

    from .state import State
    from ...libvirt import Hypervisor
    from ...libvirt.entity import Entity


class ListCommand(MatchCommand):
    '''Class for listing libvirt objects.

       This handles the required callback, as well as all the required
       options and generation of the help text.'''
    def __init__(
            self: Self,
            name: str,
            aliases: Mapping[str, MatchAlias],
            columns: Mapping[str, Column],
            default_cols: Sequence[str],
            single_list_props: tuple[str, ...] = ('name', 'uuid'),
            epilog: str | None = None,
            hidden: bool = False,
            deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        params: tuple[click.Parameter, ...] = (
            click.Option(
                param_decls=('--columns', 'cols'),
                type=ColumnsParam(columns, f'{ self.NAME } columns')(),
                nargs=1,
                help=f'A comma separated list of columns to show when listing { self.NAME }s. Use `--columns list` to list recognized column names.',
                default=default_cols,
            ),
            click.Option(
                param_decls=('--only',),
                type=click.Choice(single_list_props),
                nargs=1,
                help=f'Limit the output to a simple list of { self.NAME }s by the specified property.',
                default=None,
            ),
            click.Option(
                param_decls=('--no-headings',),
                is_flag=True,
                default=False,
                help=f'Don’t print headings when outputing the table of { self.NAME }s.',
            ),
        )

        def cb(
            ctx: click.Context,
            state: State,
            cols: Sequence[str],
            only: str | None,
            no_headings: bool,
            match: tuple[MatchTarget, re.Pattern] | None,
            parent: str | None = None
        ) -> None:
            if cols == ['list']:
                click.echo(column_info(columns, default_cols))
                ctx.exit(ExitCode.SUCCESS)

            with state.hypervisor as hv:
                if self.HAS_PARENT:
                    obj: Entity | Hypervisor = self.get_parent_obj(ctx, hv, parent)
                else:
                    obj = hv

                if match is None:
                    entities = getattr(obj, self.LOOKUP_ATTR)
                else:
                    entities = getattr(obj, self.LOOKUP_ATTR).match(match)

                if not entities and state.fail_if_no_match:
                    click.echo(f'No { self.NAME }s found matching the specified parameters.', err=True)
                    ctx.exit(ExitCode.ENTITY_NOT_FOUND)

                if only is None:
                    data = tabulate_entities(entities, columns, cols, lambda x: state.convert_units(x))
                else:
                    for e in entities:
                        click.echo(getattr(e, only))

            if only is None:
                click.echo(render_table(
                    data,
                    [columns[x] for x in cols],
                    headings=not no_headings,
                ))

        if self.HAS_PARENT:
            docstr = f'''
            List { self.NAME }s in a given { self.PARENT_NAME }.

            This will produce a (reasonably) nicely formatted table of
            { self.NAME }s in the { self.PARENT_NAME } specified by { self.PARENT_METAVAR },
            possibly limited by the specified matching parameters.'''

            params += self.mixin_parent_params()
        else:
            docstr = f'''
            List { self.NAME }s.

            This will produce a (reasonably) nicely formatted table of
            { self.NAME }s, possibly limited by the specified matching
            parameters.'''

        docstr = dedent(docstr).lstrip()

        super().__init__(
            name=name,
            help=docstr,
            aliases=aliases,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
