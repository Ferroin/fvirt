# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tabular output handling for the fvirt CLI.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Self, Type

from .terminal import get_terminal

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    import click

    from .objects import DisplayProperty
    from ...libvirt.entity import Entity


def ColumnsParam(cols: Mapping[str, DisplayProperty], type_name: str, /) -> Type[click.ParamType]:
    '''Factory funcion for creating types for column options.

       This will produce a subclass of click.ParamType for parsing a
       comma-separated list of columns based on the mapping of column
       names to columns in cols.

       The resultant class can be used with the `type` argument for
       click.option decorators to properly parse a list of columns for
       a command option.'''
    import click

    class ColumnsParam(click.ParamType):
        name = type_name

        def convert(self: Self, value: str | list[str] | None, param: Any, ctx: click.Context | None) -> list[str] | None:
            if value is None:
                return None
            elif isinstance(value, str):
                if value == 'list':
                    return ['list']
                elif value == 'all':
                    ret = [x for x in cols.keys()]
                else:
                    ret = [x.lstrip().rstrip() for x in value.split(',')]
            else:
                ret = value

            for item in ret:
                if item not in cols.keys():
                    self.fail(f'{ item } is not a valid column name. Specify a value of "list" to list known columns.', param, ctx)

            return ret

    return ColumnsParam


def column_info(columns: Mapping[str, DisplayProperty], defaults: Sequence[str], /) -> str:
    '''Produce a list of supported columns.

       Takes the column definitions that would be passed to ColumnsParam
       or render_table, together with a list of default columns, then
       produces info about the supported columns.'''
    output = 'Recognized columns:\n'

    for name in columns.keys():
        output += f'  - { name }\n'

    output += f'\nDefault columns: { ", ".join(defaults) }\n'

    return output


def color_bool(value: bool) -> str:
    '''Produce a colored string from a boolean.'''
    if value:
        return get_terminal().bright_green_on_black('Yes')
    else:
        return 'No'


def color_optional(value: Any) -> str:
    '''Format an optionally empty attribute.'''
    if value is None:
        return '-'
    else:
        return str(value)


def tabulate_entities(
    entities: Iterable[Entity],
    columns: Mapping[str, DisplayProperty],
    selected_cols: Sequence[str],
    /, *,
    convert: Callable[[int], str] = lambda x: str(x),
) -> Sequence[Sequence[str]]:
    '''Convert an iterable of entities to a list of values for columns.'''
    ret = []

    for entity in entities:
        items = []

        for column in selected_cols:
            try:
                prop = getattr(entity, columns[column].prop)
            except AttributeError:
                prop = '-'
            else:
                if columns[column].use_units:
                    prop = convert(prop)

            items.append(prop)

        ret.append(items)

    return ret


def render_table(items: Sequence[Sequence[Any]], columns: Sequence[DisplayProperty], headings: bool = True) -> str:
    '''Render a table of items.

       `items` should be a list of rows, where each row is a list of
       strings corresponding to the values for each column in that row.

       `columns` is a list of corresponding Column instances for the
       columns to be used for the table.'''
    ret = ''
    TERM: Final = get_terminal()

    column_sizes = [
        max([
            TERM.length(columns[i].color(row[i])) for row in items
        ]) for i in range(0, len(columns))
    ]

    if headings:
        column_sizes = [
            max(column_sizes[i], len(columns[i].title)) for i in range(0, len(columns))
        ]

        for idx, column in enumerate(columns):
            if columns[idx].right_align:
                ret += f'  {column.title:>{column_sizes[idx]}}'
            else:
                ret += f'  {column.title:<{column_sizes[idx]}}'

        ret += '\n'
        ret += (TERM.bold('-' * (sum(column_sizes) + (2 * len(column_sizes)))))
        ret += '\n'

    for row in items:
        for idx, item in enumerate(row):
            if columns[idx].right_align:
                ret += f'  {TERM.rjust(columns[idx].color(item), width=column_sizes[idx])}'
            else:
                ret += f'  {TERM.ljust(columns[idx].color(item), width=column_sizes[idx])}'

        ret += '\n'

    return ret.rstrip()


__all__ = [
    'ColumnsParam',
    'color_bool',
    'color_optional',
    'column_info',
    'tabulate_entities',
    'render_table',
]
