# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Common functions and definitions used throughout virshx.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

import math


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


def render_table(items: list[list[str]], columns: list[Column]) -> str:
    '''Render a table of items.

       `items` should be a list of rows, where each row is a list of
       strings corresponding to the values for each column in that row.

       `columns` is a list of corresponding Column instances for the
       columns to be used for the table.'''
    ret = ''

    column_sizes = [
        max([
            len(row[i]) for row in items
        ] + [len(columns[i].title)]) for i in range(0, len(columns))
    ]

    for idx, column in enumerate(columns):
        if columns[idx].right_align:
            ret += f' {column.title:>{column_sizes[idx]}}'
        else:
            ret += f' {column.title:<{column_sizes[idx]}}'

    ret += '\n'
    ret += ('-' * (sum(column_sizes) + 4))
    ret += '\n'

    for row in items:
        for idx, item in enumerate(row):
            if columns[idx].right_align:
                ret += f' {item:>{column_sizes[idx]}}'
            else:
                ret += f' {item:<{column_sizes[idx]}}'

        ret += '\n'

    return ret


__all__ = [
    'VERSION',
    'VersionNumber',
    'VirshxException',
    'unit_to_bytes',
    'Column',
    'render_table',
]
