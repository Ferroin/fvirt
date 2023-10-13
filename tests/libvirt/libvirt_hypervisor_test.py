# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.hypervisor'''

from __future__ import annotations

from typing import cast

import pytest

from fvirt.libvirt.entity_access import EntityAccess
from fvirt.libvirt.hypervisor import Hypervisor
from fvirt.libvirt.uri import LIBVIRT_DEFAULT_URI, URI
from fvirt.version import VersionNumber


def test_init(test_hv: Hypervisor) -> None:
    '''Test initialization of a Hypervisor.'''
    assert isinstance(test_hv, Hypervisor)


def test_manual_connect(test_hv: Hypervisor) -> None:
    '''Test basic open and close method usage.'''
    assert not test_hv.connected

    hv2 = test_hv.open()

    assert test_hv == hv2
    assert cast(bool, test_hv.connected)

    hv3 = test_hv.open()

    assert hv2 == hv3
    assert cast(bool, test_hv.connected)

    test_hv.close()

    assert cast(bool, test_hv.connected)

    test_hv.close()

    assert not cast(bool, test_hv.connected)

    test_hv.close()

    assert not cast(bool, test_hv.connected)


def test_context_manager(test_hv: Hypervisor) -> None:
    '''Test that the context manager protocol works.'''
    assert not test_hv.connected

    with test_hv:
        assert cast(bool, test_hv.connected)

        with test_hv:
            assert cast(bool, test_hv.connected)

        assert cast(bool, test_hv.connected)

    assert not cast(bool, test_hv.connected)


def test_read_only(test_uri: str) -> None:
    '''Test the read-only property.'''
    test_hv = Hypervisor(hvuri=URI.from_string(test_uri), read_only=True)

    assert test_hv.read_only

    with pytest.raises(AttributeError):
        test_hv.read_only = False  # type: ignore


def test_uri(test_hv: Hypervisor, test_uri: str) -> None:
    '''Test the uri property.'''
    assert isinstance(test_hv.uri, URI)
    assert str(test_hv.uri) == test_uri

    with pytest.raises(AttributeError):
        test_hv.uri = LIBVIRT_DEFAULT_URI  # type: ignore


def test_libVersion(test_hv: Hypervisor) -> None:
    '''Test that the libVersion property is a VersionNumber.'''
    assert isinstance(test_hv.libVersion, VersionNumber)

    with pytest.raises(AttributeError):
        test_hv.libVersion = VersionNumber(0, 0, 0)  # type: ignore


def test_version(test_hv: Hypervisor) -> None:
    '''Test that the version property is a VersionNumber.'''
    assert isinstance(test_hv.version, VersionNumber)

    with pytest.raises(AttributeError):
        test_hv.version = VersionNumber(0, 0, 0)  # type: ignore


@pytest.mark.parametrize('t', (
    'domains',
    'pools',
))
def test_entities(test_hv: Hypervisor, t: str) -> None:
    '''Check that entity access attributes exist.'''
    assert hasattr(test_hv, t)

    assert isinstance(getattr(test_hv, t), EntityAccess)
