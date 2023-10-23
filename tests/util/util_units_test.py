# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.units'''

from __future__ import annotations

import pytest

from fvirt.util.units import IEC_FACTOR_TO_NAME, NAME_TO_FACTOR, SI_FACTOR_TO_NAME, bytes_to_unit, unit_to_bytes


def test_name_mapping() -> None:
    '''Confirm that the name to factor mapping is valid.'''
    for k, v in NAME_TO_FACTOR.items():
        assert isinstance(k, str)
        assert isinstance(v, int)


def test_si_units() -> None:
    '''Confirm that the SI unit mapping is valid.'''
    last_k = 0

    for k, v in SI_FACTOR_TO_NAME.items():
        assert isinstance(k, int)
        assert isinstance(v, str)
        assert k > last_k
        last_k = k
        assert NAME_TO_FACTOR[v] == k


def test_iec_units() -> None:
    '''Confirm that the IEC unit mapping is valid.'''
    last_k = 0

    for k, v in IEC_FACTOR_TO_NAME.items():
        assert isinstance(k, int)
        assert isinstance(v, str)
        assert k > last_k
        last_k = k
        assert NAME_TO_FACTOR[v] == k


def test_convert_wrong_value_type() -> None:
    '''Test that value errors are raised appropriately.'''
    with pytest.raises(TypeError, match=' is not an integer or float'):
        unit_to_bytes('', 'B')  # type: ignore


def test_convert_negative_value() -> None:
    '''Test that negative values are rejected.'''
    with pytest.raises(ValueError, match='Conversion is only supported for positive values.'):
        unit_to_bytes(-1, 'B')


@pytest.mark.parametrize('u, e', (
    (k, v) for k, v in NAME_TO_FACTOR.items()
))
def test_conversion(u: str, e: int) -> None:
    '''Test that unit conversion works correctly.'''
    assert unit_to_bytes(1, u) == e


def test_invalid_unit() -> None:
    '''Test that an invalid unit throws an error.'''
    with pytest.raises(ValueError, match='Unrecognized unit name'):
        unit_to_bytes(1, 'invalid') == NotImplemented


def test_back_convert_invalid_type() -> None:
    '''Test that type errors are raised appropriately.'''
    with pytest.raises(TypeError, match='Value must be an integer.'):
        bytes_to_unit(1.0)  # type: ignore

    with pytest.raises(TypeError, match='Value must be an integer.'):
        bytes_to_unit('')  # type: ignore


def test_back_convert_invalid_value() -> None:
    '''Test that value errors are raised appropriately.'''
    with pytest.raises(ValueError, match='Value must be a positive integer.'):
        bytes_to_unit(-1)


@pytest.mark.parametrize('v, e', (
    (k, v) for k, v in SI_FACTOR_TO_NAME.items()
))
def test_si_back_conversion(v: int, e: str) -> None:
    '''Test that back-converting to SI units works correctly.'''
    value, unit = bytes_to_unit(v, iec=False)

    assert isinstance(value, float)
    assert value == pytest.approx(1.0)
    assert unit == e

    value, unit = bytes_to_unit(v * 2, iec=False)

    assert isinstance(value, float)
    assert value == pytest.approx(2.0)
    assert unit == e


@pytest.mark.parametrize('v, e', (
    (k, v) for k, v in IEC_FACTOR_TO_NAME.items()
))
def test_iec_back_conversion(v: int, e: str) -> None:
    '''Test that back-converting to IEC units works correctly.'''
    value, unit = bytes_to_unit(v, iec=True)

    assert isinstance(value, float)
    assert value == pytest.approx(1.0)
    assert unit == e

    value, unit = bytes_to_unit(v * 2, iec=True)

    assert isinstance(value, float)
    assert value == pytest.approx(2.0)
    assert unit == e


def test_si_zero_back_conversion() -> None:
    '''Test that converting 0 to SI units works correctly.'''
    value, unit = bytes_to_unit(0, iec=False)

    assert isinstance(value, float)
    assert value == pytest.approx(0.0)
    assert unit == 'B'


def test_iec_zero_back_conversion() -> None:
    '''Test that converting 0 to IEC units works correctly.'''
    value, unit = bytes_to_unit(0, iec=True)

    assert isinstance(value, float)
    assert value == pytest.approx(0.0)
    assert unit == 'B'
