# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Common functions and definitions used throughout virshx.'''

from __future__ import annotations

import math

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, Type, Any

import blessed
import click

if TYPE_CHECKING:
    from collections.abc import Callable

TERM = blessed.Terminal()


class VersionNumber:
    '''Minimal wrapper class for version information.'''
    def __init__(self: Self, major: int, minor: int, release: int) -> None:
        self.__major = major
        self.__minor = minor
        self.__release = release

    def __repr__(self: Self) -> str:
        return f'{ self.major }.{ self.minor }.{ self.release }'

    def __str__(self: Self) -> str:
        return repr(self)

    def __getitem__(self: Self, idx: int) -> int:
        match idx:
            case 0:
                return self.major
            case 1:
                return self.minor
            case 2:
                return self.release
            case _:
                raise IndexError

    @property
    def major(self: Self) -> int:
        '''The major version number.'''
        return self.__major

    @property
    def minor(self: Self) -> int:
        '''The minor version number.'''
        return self.__minor

    @property
    def release(self: Self) -> int:
        '''The release release number.'''
        return self.__release


VERSION = VersionNumber(0, 0, 1)


class VirshxException(Exception):
    '''Base exception for all virshx exceptions.'''
    pass


def unit_to_bytes(value: int | float, unit: str) -> int:
    '''Convert a value with units to integral bytes.

       Conversion rules for the unit are the same as used by libvirt in
       their XML configuration files.

       Unrecongized values for unit will return NotImplemented.

       If value is less than 0, a ValueError will be raised.

       If the conversion would return a fractional number of bytes,
       the result is rounded up.'''
    if not (isinstance(value, int) or isinstance(value, float)):
        raise ValueError(f'{ value } is not an integer or float.')
    elif value < 0:
        raise ValueError('Conversion is only supported for positive values.')

    match unit:
        case 'B' | 'bytes':
            ret = value
        case 'KB':
            ret = value * (10 ** 3)
        case 'K' | 'KiB':
            ret = value * (2 ** 10)
        case 'MB':
            ret = value * (10 ** 6)
        case 'M' | 'MiB':
            ret = value * (2 ** 20)
        case 'GB':
            ret = value * (10 ** 9)
        case 'G' | 'GiB':
            ret = value * (2 ** 30)
        case 'TB':
            ret = value * (10 ** 12)
        case 'T' | 'TiB':
            ret = value * (2 ** 40)
        case 'PB':
            ret = value * (10 ** 15)
        case 'P' | 'PiB':
            ret = value * (2 ** 50)
        case 'EB':
            ret = value * (10 ** 18)
        case 'E' | 'EiB':
            ret = value * (2 ** 60)
        case _:
            return NotImplemented

    return math.ceil(ret)


@dataclass(kw_only=True, slots=True)
class Column:
    '''Data class representing column configuration for table rendering.'''
    title: str
    prop: str
    right_align: bool = False
    color: Callable[[Any], str] = lambda x: str(x)


def ColumnsParam(cols: dict[str, Column], type_name: str) -> Type[click.ParamType]:
    '''Factory funcion for creating types for column options.

       This will produce a subclass of click.ParamType for parsing a
       comma-separated list of columns based on the mapping of column
       names to columns in cols.

       The resultant class can be used with the `type` argument for
       click.option decorators to properly parse a list of columns for
       a command option.'''
    class ColumnsParam(click.ParamType):
        name = type_name

        def convert(self: Self, value: str | list[str], param: Any, ctx: click.core.Context | None) -> list[str]:
            if isinstance(value, str):
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


def print_columns(columns: dict[str, Column], defaults: list[str]) -> None:
    '''Print out a list of supported columns.

       Takes the column definitions that would be passed to ColumnsParam
       or render_table, together with a list of default columns, then
       uses click to print out info about supported columns.'''
    output = 'Recognized columns:\n'

    for name in columns.keys():
        output += f'  - { name }\n'

    output += f'\nDefault columns: { ", ".join(defaults) }\n'

    click.echo(output)


def color_bool(value: bool) -> str:
    '''Produce a colored string from a boolean.'''
    if value:
        return TERM.bright_green_on_black('Yes')
    else:
        return 'No'


def render_table(items: list[list[str]], columns: list[Column]) -> str:
    '''Render a table of items.

       `items` should be a list of rows, where each row is a list of
       strings corresponding to the values for each column in that row.

       `columns` is a list of corresponding Column instances for the
       columns to be used for the table.'''
    ret = ''

    column_sizes = [
        max([
            len(str(row[i])) for row in items
        ] + [len(columns[i].title)]) for i in range(0, len(columns))
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

    return ret


__all__ = [
    'VERSION',
    'TERM',
    'VersionNumber',
    'VirshxException',
    'unit_to_bytes',
    'Column',
    'ColumnsParam',
    'print_columns',
    'color_bool',
    'render_table',
]
