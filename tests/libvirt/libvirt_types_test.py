# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.types.'''

from __future__ import annotations

import datetime

from typing import Any

import pytest

from fvirt.libvirt.types import CustomBool, OnOff, Timestamp, YesNo


@pytest.mark.parametrize('t, true_str, false_str', (
    (OnOff, 'on', 'off'),
    (YesNo, 'yes', 'no'),
))
def test_custom_bools(t: type[CustomBool], true_str: str, false_str: str) -> None:
    '''Test custom boolean types.'''
    assert bool(t(true_str))
    assert not bool(t(false_str))
    assert bool(t(True))
    assert not bool(t(False))
    assert bool(t(t(true_str)))
    assert not bool(t(t(false_str)))

    cb_t = t(True)
    cb_f = t(False)

    assert cb_t == t(true_str)
    assert cb_f == t(false_str)
    assert cb_t == True  # noqa: E712
    assert cb_f == False  # noqa: E712
    assert cb_t == true_str
    assert cb_f == false_str
    assert cb_t != ''
    assert cb_f != ''
    assert cb_t != []
    assert cb_f != []

    assert str(cb_t) == true_str
    assert str(cb_f) == false_str

    assert hash(cb_t) == hash(True)
    assert hash(cb_f) == hash(False)


def test_Timestamp_invalid_init() -> None:
    '''Test that invalid Timestamp initializers are rejected.'''
    with pytest.raises(ValueError):
        Timestamp('')

    with pytest.raises(ValueError):
        Timestamp(None)  # type: ignore

    with pytest.raises(ValueError):
        Timestamp([])  # type: ignore


@pytest.mark.parametrize('v, t, e', (
    (0, int, 0),
    (0, float, 0.0),
    (0, str, '1970-01-01T00:00:00'),
    ('1970-01-01T00:00:00Z', int, 0),
    ('1970-01-01T00:00:00Z', float, 0.0),
    ('1970-01-01T00:00:00Z', str, '1970-01-01T00:00:00'),
    (datetime.datetime.fromisoformat('1970-01-01T00:00:00Z'), int, 0),
    (datetime.datetime.fromisoformat('1970-01-01T00:00:00Z'), float, 0.0),
    (datetime.datetime.fromisoformat('1970-01-01T00:00:00Z'), str, '1970-01-01T00:00:00'),
    (datetime.date.fromisoformat('1970-01-01'), int, 0),
    (datetime.date.fromisoformat('1970-01-01'), float, 0.0),
    (datetime.date.fromisoformat('1970-01-01'), str, '1970-01-01T00:00:00'),
))
def test_Timestamp_conversion(v: int | str | datetime.datetime, t: type[int | str | float], e: int | str | float) -> None:
    '''Check base type conversion handling for Timestamps.'''
    tstamp = Timestamp(v)

    assert t(tstamp) == e


@pytest.mark.parametrize('v, e', (
    (0, (
        0,
        0.0,
        '1970-01-01T00:00:00',
        datetime.datetime.fromisoformat('1970-01-01T00:00:00Z'),
    )),
    (1, (
        1,
        1.0,
        '1970-01-01T00:00:01',
        datetime.datetime.fromisoformat('1970-01-01T00:00:01Z'),
    )),
    (60, (
        60,
        60.0,
        '1970-01-01T00:01:00',
        datetime.datetime.fromisoformat('1970-01-01T00:01:00Z'),
    )),
))
def test_Timestamp_equality(v: int, e: tuple[Any]) -> None:
    '''Check Timestamp equality checking.'''
    tstamp = Timestamp(v)

    assert tstamp == Timestamp(v)

    for x in e:
        assert tstamp == x


def test_Timestamp_not_equal() -> None:
    '''Check invalid equality cases for Timestamp instances.'''
    assert Timestamp(0) != []
    assert Timestamp(0) != ''


@pytest.mark.parametrize('v', (
    0,
    1,
    60,
    3600,
))
def test_Timestamp_hash(v: int) -> None:
    '''Check Timestamp hash behavior.'''
    tstamp = Timestamp(v)

    assert hash(tstamp) == hash(tstamp.datetime)


def test_Timestamp_ordering() -> None:
    '''Check ordering comparisons for Timestamps.'''
    tstamp1 = Timestamp(0)
    tstamp2 = Timestamp(1)

    assert tstamp1 != tstamp2
    assert tstamp1 < tstamp2
    assert tstamp1 <= tstamp2
    assert tstamp2 <= tstamp2
    assert tstamp2 > tstamp1
    assert tstamp2 >= tstamp1
    assert tstamp1 >= tstamp1


def test_Timestamp_comparison() -> None:
    '''Check ordering comparisons between Timestamps and other types.'''
    tstamp = Timestamp(1)

    assert tstamp < datetime.datetime.fromisoformat('1970-01-01T00:01:00')
    assert tstamp > datetime.date.fromisoformat('1970-01-01')

    assert tstamp < 2
    assert tstamp > 0

    assert tstamp < '1970-01-01T00:01:00'
    assert tstamp > '1970-01-01'

    assert tstamp.__lt__('') is NotImplemented
    assert tstamp.__lt__([]) is NotImplemented


def test_Timestamp_datetime() -> None:
    '''Check the datetime property for Timestamps.'''
    tstamp = Timestamp(0)

    assert tstamp.datetime == datetime.datetime.fromisoformat('1970-01-01T00:00:00Z')
