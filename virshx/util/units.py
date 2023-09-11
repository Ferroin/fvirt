# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Unit handling for virshx code.'''

from __future__ import annotations

import math


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


__all__ = [
    'unit_to_bytes',
]
