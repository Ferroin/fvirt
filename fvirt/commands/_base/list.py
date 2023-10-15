# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that list objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Self

import click

from .match import MatchCommand
from ...util.match import MatchAlias, MatchTarget
from ...util.tables import Column, ColumnsParam, print_columns, render_table, tabulate_entities

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping, Sequence

    from .state import State


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
            doc_name: str,
            hvprop: str,
            single_list_props: tuple[str, ...] = ('name', 'uuid'),
            obj_prop: str | None = None,
            obj_name: str | None = None,
            hvmetavar: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        params = tuple(params) + (
            click.Option(
                param_decls=('--columns', 'cols'),
                type=ColumnsParam(columns, f'{ doc_name } columns')(),
                nargs=1,
                help=f'A comma separated list of columns to show when listing { doc_name }s. Use `--columns list` to list recognized column names.',
                default=default_cols,
            ),
            click.Option(
                param_decls=('--only',),
                type=click.Choice(single_list_props),
                nargs=1,
                help=f'Limit the output to a simple list of { doc_name }s by the specified property.',
                default=None,
            ),
            click.Option(
                param_decls=('--no-headings',),
                is_flag=True,
                default=False,
                help=f'Don’t print headings when outputing the table of { doc_name }s.',
            ),
        )

        def cb(
            ctx: click.Context,
            state: State,
            cols: Sequence[str],
            only: str | None,
            no_headings: bool,
            match: tuple[MatchTarget, re.Pattern] | None,
            name: str | None = None
        ) -> None:
            if cols == ['list']:
                print_columns(columns, default_cols)
                ctx.exit(0)

            with state.hypervisor as hv:
                if obj_prop is None:
                    obj = hv
                    prop = hvprop
                else:
                    assert obj_prop is not None

                    obj = getattr(hv, hvprop).get(name)
                    prop = obj_prop

                    if obj is None:
                        ctx.fail(f'No { obj_name } with name, UUID, or ID of "{ name }" is defined on this hypervisor.')

                if match is None:
                    entities = getattr(obj, prop)
                else:
                    entities = getattr(obj, prop).match(match)

                if not entities and state.fail_if_no_match:
                    ctx.fail('No { doc_name }s found matching the specified parameters.')

                if only is None:
                    data = tabulate_entities(entities, columns, cols)
                else:
                    for e in entities:
                        click.echo(getattr(e, only))

            if only is None:
                click.echo(render_table(
                    data,
                    [columns[x] for x in cols],
                    headings=not no_headings,
                ))

        if obj_prop is None:
            docstr = f'''
            List { doc_name }s.

            This will produce a (reasonably) nicely formatted table of
            { doc_name }s, possibly limited by the specified matching
            parameters.'''
        else:
            assert obj_name is not None
            assert hvmetavar is not None

            docstr = f'''
            List { doc_name }s in a given { obj_name }.

            This will produce a (reasonably) nicely formatted table of
            { doc_name }s in the { obj_name } specified by { hvmetavar },
            possibly limited by the specified matching parameters.'''

            params += (click.Argument(
                param_decls=('name',),
                metavar=hvmetavar,
                nargs=1,
                required=True,
            ),)

        docstr = dedent(docstr).lstrip()

        super().__init__(
            name=name,
            help=docstr,
            aliases=aliases,
            epilog=epilog,
            callback=cb,
            doc_name=doc_name,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
