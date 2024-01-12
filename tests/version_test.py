# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.version'''

import pytest

import fvirt

from fvirt.version import VersionNumber


def test_version_type() -> None:
    '''Confirm that VERSION is a VersionNumber.'''
    assert isinstance(fvirt.VERSION, VersionNumber)


def test_equality() -> None:
    '''Confirm that VersionNumber equality testing works.'''
    assert VersionNumber(0, 1, 0) == VersionNumber(0, 1, 0)
    assert '0.1.0' != VersionNumber(0, 1, 0)


def test_version_props() -> None:
    '''Test that VersionNumber properties map to arguments.'''
    v = VersionNumber(1, 2, 3)

    assert v.major == 1
    assert v.minor == 2
    assert v.release == 3


def test_version_index() -> None:
    '''Test that index access works for VersionNumbers.'''
    v = VersionNumber(1, 2, 3)

    assert v[0] == 1
    assert v[-3] == 1
    assert v[1] == 2
    assert v[-2] == 2
    assert v[2] == 3
    assert v[-1] == 3

    with pytest.raises(IndexError):
        v[3]

    with pytest.raises(IndexError):
        v[-4]


def test_invalid_args() -> None:
    '''Test that negative arguments throw errors.'''
    with pytest.raises(ValueError, match='Major version number must be non-negative.'):
        VersionNumber(-1, 2, 3)

    with pytest.raises(ValueError, match='Minor version number must be non-negative.'):
        VersionNumber(1, -2, 3)

    with pytest.raises(ValueError, match='Release number must be non-negative.'):
        VersionNumber(1, 2, -3)


def test_version_str() -> None:
    '''Test that conversion to a string works correctly.'''
    assert str(fvirt.VERSION) == f'{ fvirt.VERSION.major }.{ fvirt.VERSION.minor }.{ fvirt.VERSION.release }'


def test_version_hash() -> None:
    '''Confirm that VersionNumber instances are hashable.'''
    assert isinstance(hash(VersionNumber(1, 2, 3)), int)


@pytest.mark.parametrize('v, t', (
    (0, VersionNumber(0, 0, 0)),
    (1, VersionNumber(0, 0, 1)),
    (1000, VersionNumber(0, 1, 0)),
    (1000000, VersionNumber(1, 0, 0)),
))
def test_VersionNumber_libvirt_parse(v: int, t: VersionNumber) -> None:
    '''Test that parsing libvirt version numbers works correctly.'''
    assert VersionNumber.from_libvirt_version(v) == t


def test_VersionNumber_order() -> None:
    '''Test ordering of VersionNumbers.'''
    v1 = VersionNumber(0, 0, 0)
    v2 = VersionNumber(1, 0, 0)
    v3 = VersionNumber(0, 1, 0)
    v4 = VersionNumber(0, 0, 1)
    v5 = VersionNumber(1, 1, 0)
    v6 = VersionNumber(0, 1, 1)

    assert v1 < v2
    assert v2 > v3
    assert v3 > v4
    assert v2 < v5
    assert v3 < v6


def test_VersionNumber_len() -> None:
    '''Test the length of a VersionNumber.'''
    assert len(VersionNumber(1, 2, 3)) == 3


def test_VersionNumber_iter() -> None:
    '''Test use of a VersionNumber as an iterator.'''
    for i, j in zip(
        VersionNumber(1, 2, 3),
        (1, 2, 3),
    ):
        assert i == j
