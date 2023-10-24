# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Unit handling for fvirt code.'''

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Final

from frozendict import frozendict

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

NAME_TO_FACTOR: Final = frozendict({
    'B': 1,
    'bytes': 1,
    'KB': 10 ** 3,
    'K': 2 ** 10,
    'KiB': 2 ** 10,
    'MB': 10 ** 6,
    'M': 2 ** 20,
    'MiB': 2 ** 20,
    'GB': 10 ** 9,
    'G': 2 ** 30,
    'GiB': 2 ** 30,
    'TB': 10 ** 12,
    'T': 2 ** 40,
    'TiB': 2 ** 40,
    'PB': 10 ** 15,
    'P': 2 ** 50,
    'PiB': 2 ** 50,
    'EB': 10 ** 18,
    'E': 2 ** 60,
    'EiB': 2 ** 60,
})

SI_FACTOR_TO_NAME: Final = frozendict({
    1: 'B',
    10 ** 3: 'KB',
    10 ** 6: 'MB',
    10 ** 9: 'GB',
    10 ** 12: 'TB',
    10 ** 15: 'PB',
    10 ** 18: 'EB',
})

IEC_FACTOR_TO_NAME: Final = frozendict({
    1: 'B',
    2 ** 10: 'KiB',
    2 ** 20: 'MiB',
    2 ** 30: 'GiB',
    2 ** 40: 'TiB',
    2 ** 50: 'PiB',
    2 ** 60: 'EiB',
})


def unit_to_bytes(value: int | float, unit: str) -> int:
    '''Convert a value with units to integral bytes.

       Conversion rules for the unit are the same as used by libvirt in
       their XML configuration files.

       Unrecongized values for unit will raise a ValueError.

       If value is less than 0, a ValueError will be raised.

       If the conversion would return a fractional number of bytes,
       the result is rounded up.'''
    if not (isinstance(value, int) or isinstance(value, float)):
        raise TypeError(f'{ value } is not an integer or float.')
    elif value < 0:
        raise ValueError('Conversion is only supported for positive values.')

    factor = NAME_TO_FACTOR.get(unit, None)

    if factor is None:
        raise ValueError(f'Unrecognized unit name "{ unit }".')

    return math.ceil(value * factor)


def __get_factor(value: int, factors: Iterable[int]) -> int:
    ret = 1

    for f in factors:
        if f > value:
            break

        ret = f

    return ret


def bytes_to_unit(value: int, /, *, iec: bool = False) -> tuple[float, str]:
    '''Convert a number of bytes to an appropriate larger unit.

       Returns a tuple of the converted value and the unit name.

       The target unit will be determined based on the magnitude of
       the vaule such that no more than three digits before the decimal
       point are present after conversion (unless the value is too large).

       By default, SI units will be used. If `iec` is True, then IEC
       units will be used instead.

       If the value is less than 0, a ValueError will be raised.'''
    if not isinstance(value, int):
        raise TypeError('Value must be an integer.')
    elif value < 0:
        raise ValueError('Value must be a positive integer.')

    factors = SI_FACTOR_TO_NAME

    if iec:
        factors = IEC_FACTOR_TO_NAME

    factor = __get_factor(value, factors.keys())

    return (
        value / factor,
        factors[factor],
    )


__all__ = [
    'unit_to_bytes',
]
