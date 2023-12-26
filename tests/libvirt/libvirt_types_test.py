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

    assert str(t(true_str)) == true_str
    assert str(t(false_str)) == false_str
    assert str(t(True)) == true_str
    assert str(t(False)) == false_str

    assert hash(t(true_str)) == hash(True)
    assert hash(t(false_str)) == hash(False)
    assert hash(t(True)) == hash(True)
    assert hash(t(False)) == hash(False)


@pytest.mark.parametrize('v, t, e', (
    (0, int, 0),
    (0, float, 0.0),
    (0, str, '1970-01-01T00:00:00'),
    ('1970-01-01T00:00:00Z', int, 0),
    ('1970-01-01T00:00:00Z', float, 0.0),
    ('1970-01-01T00:00:00Z', str, '1970-01-01T00:00:00'),
))
def test_Timestamp_conversion(v: int | str | datetime.datetime, t: type[int | str | float], e: int | str | float) -> None:
    '''Check base type conversion handling for Timestamps.'''
    tstamp = Timestamp(v)

    assert t(tstamp) == e


@pytest.mark.parametrize('v, e', (
    (0, (0, 0.0, '1970-01-01T00:00:00', datetime.datetime.fromisoformat('1970-01-01T00:00:00Z'))),
    (1, (1, 1.0, '1970-01-01T00:00:01', datetime.datetime.fromisoformat('1970-01-01T00:00:01Z'))),
    (60, (60, 60.0, '1970-01-01T00:01:00', datetime.datetime.fromisoformat('1970-01-01T00:01:00Z'))),
))
def test_Timestamp_equality(v: int, e: tuple[Any]) -> None:
    '''Check Timestamp equality checking.'''
    tstamp = Timestamp(v)

    assert tstamp == Timestamp(v)

    for x in e:
        assert tstamp == x


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


def test_Timestamp_datetime() -> None:
    '''Check the datetime property for Timestamps.'''
    tstamp = Timestamp(0)

    assert tstamp.datetime == datetime.datetime.fromisoformat('1970-01-01T00:00:00Z')
