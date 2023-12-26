# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that list objects.'''

from __future__ import annotations

import logging

from textwrap import dedent
from typing import TYPE_CHECKING, Final, Self

import click

from .exitcode import ExitCode
from .match import MatchCommand
from .objects import is_object_mixin
from .tables import ColumnsParam, column_info, render_table, tabulate_entities
from ...util.match import MatchArgument

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .state import State
    from ...libvirt import Hypervisor
    from ...libvirt.entity import Entity

LOGGER: Final = logging.getLogger(__name__)


class ListCommand(MatchCommand):
    '''Class for listing libvirt objects.

       This handles the required callback, as well as all the required
       options and generation of the help text.'''
    def __init__(
            self: Self,
            name: str,
            epilog: str | None = None,
            hidden: bool = False,
            deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        params: tuple[click.Parameter, ...] = (
            click.Option(
                param_decls=('--columns', 'selected'),
                type=ColumnsParam(self.DISPLAY_PROPS, f'{ self.NAME } columns')(),
                nargs=1,
                help=f'A comma separated list of columns to show when listing { self.NAME }s. Use `--columns list` to list recognized column names.',
                default=self.DEFAULT_COLUMNS,
            ),
            click.Option(
                param_decls=('--only',),
                type=click.Choice(list(self.SINGLE_LIST_PROPS)),
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
            selected: Sequence[str],
            only: str | None,
            no_headings: bool,
            match: MatchArgument | None,
            parent: str | None = None
        ) -> None:
            if selected == ['list']:
                click.echo(column_info(self.DISPLAY_PROPS, self.DEFAULT_COLUMNS))
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
                    LOGGER.warning(f'No { self.NAME }s found matching the specified parameters.')
                    ctx.exit(ExitCode.ENTITY_NOT_FOUND)

                if only is None:
                    data = tabulate_entities(entities, self.DISPLAY_PROPS, selected, convert=lambda x: state.convert_units(x))
                else:
                    for e in entities:
                        click.echo(getattr(e, only))

            if only is None:
                click.echo(render_table(
                    data,
                    [self.DISPLAY_PROPS[x] for x in selected],
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
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
