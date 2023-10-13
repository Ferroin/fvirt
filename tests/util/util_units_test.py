# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.units'''

from __future__ import annotations

import pytest

from fvirt.util.units import unit_to_bytes


def test_wrong_value_type() -> None:
    '''Test that value errors are raised appropriately.'''
    with pytest.raises(ValueError, match=' is not an integer or float'):
        unit_to_bytes('', 'B')  # type: ignore


def test_negative_value() -> None:
    '''Test that negative values are rejected.'''
    with pytest.raises(ValueError, match='Conversion is only supported for positive values.'):
        unit_to_bytes(-1, 'B')


@pytest.mark.parametrize('u, e', (
    ('B', 1),
    ('bytes', 1),
    ('KB', 10**3),
    ('K', 2**10),
    ('KiB', 2**10),
    ('MB', 10**6),
    ('M', 2**20),
    ('MiB', 2**20),
    ('GB', 10**9),
    ('G', 2**30),
    ('GiB', 2**30),
    ('TB', 10**12),
    ('T', 2**40),
    ('TiB', 2**40),
    ('PB', 10**15),
    ('P', 2**50),
    ('PiB', 2**50),
    ('EB', 10**18),
    ('E', 2**60),
    ('EiB', 2**60),
))
def test_conversion(u: str, e: int) -> None:
    '''Test that unit conversion works correctly.'''
    assert unit_to_bytes(1, u) == e


def test_invalid_unit() -> None:
    '''Test that an invalid unit returns NotImplemented.'''
    assert unit_to_bytes(1, 'invalid') == NotImplemented
