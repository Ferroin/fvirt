# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that list objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self

import click

from .match import MatchCommand
from ...libvirt import Hypervisor
from ...util.match import MatchAlias, MatchTarget
from ...util.tables import Column, ColumnsParam, print_columns, render_table, tabulate_entities

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping, MutableMapping, Sequence


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
            obj_prop: str | None = None,
            obj_name: str | None = None,
            hvmetavar: str | None = None,
            epilog: str | None = None,
            params: Sequence[click.Parameter] = [],
            context_settings: MutableMapping[str, Any] = dict(),
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        params = tuple(params) + (click.Option(
            param_decls=('--columns', 'cols'),
            type=ColumnsParam(columns, f'{ doc_name } columns')(),
            nargs=1,
            help=f'A comma separated list of columns to show when listing { doc_name }s. Use `--columns list` to list recognized column names.',
            default=default_cols,
        ),)

        def cb(ctx: click.Context, cols: Sequence[str], match: tuple[MatchTarget, re.Pattern] | None, name: str | None = None) -> None:
            if cols == ['list']:
                print_columns(columns, default_cols)
                ctx.exit(0)

            with Hypervisor(hvuri=ctx.obj['uri']) as hv:
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

                if not entities and ctx.obj['fail_if_no_match']:
                    ctx.fail('No { doc_name }s found matching the specified parameters.')

                data = tabulate_entities(entities, columns, cols)

            output = render_table(
                data,
                [columns[x] for x in cols],
            )

            click.echo(output)

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
            context_settings=context_settings,
            hidden=hidden,
            deprecated=deprecated,
        )
