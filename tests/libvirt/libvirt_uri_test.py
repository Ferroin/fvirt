# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.uri'''

import pytest

from fvirt.libvirt.uri import CLIENT_ONLY_DRIVERS, SESSION_DRIVERS, SYSTEM_DRIVERS, URI

# Definitions used below
CLIENT_ONLY_DRIVER = sorted(CLIENT_ONLY_DRIVERS, key=lambda x: x.value)[0].value
SESSION_DRIVER = sorted(SESSION_DRIVERS - SYSTEM_DRIVERS, key=lambda x: x.value)[0].value
SYSTEM_DRIVER = sorted(SYSTEM_DRIVERS - SESSION_DRIVERS, key=lambda x: x.value)[0].value

# An assortment of cannonical URIs used for the tests.
SAMPLE_URIS = (
    'openvz+ssh://root@example.com/system',
    'qemu:///system',
    'test:///default',
    'vbox+tcp://user@example.com/session',
    'xen://example.com/system',
    'hyperv://example-hyperv.com/?transport=http',
    'ch:///session',
    'bhyve+ext://example.com/system?command=nc',
)

# An assortment of known invalid URIs used for tests.
# Each of these should test _exactly_ one failure mode.
BAD_URIS = (
    'foo:///',  # Bogus driver
    'qemu+bar:///system',  # Bogus transport
    'xen://example.com:0/',  # Invalid port number
    'test+ext:///defaults',  # Ext driver without command.
    f'{ CLIENT_ONLY_DRIVER }+ssh://example.com/',  # Client-only driver with transport
    f'{ CLIENT_ONLY_DRIVER }:///',  # Client-only driver without host
    f'{ SESSION_DRIVER }:///system',  # Using system with session driver
    f'{ SYSTEM_DRIVER }:///session',  # Using session with system driver
)


@pytest.mark.parametrize('uri', SAMPLE_URIS)
def test_check_validity(uri: str) -> None:
    '''Check that known valid URIs pass our validation.'''
    assert isinstance(URI.from_string(uri), URI)


@pytest.mark.parametrize('uri', BAD_URIS)
def test_check_invalid(uri: str) -> None:
    '''Check that known invalid URIs are treated as such.'''
    with pytest.raises(ValueError):
        URI.from_string(uri)


@pytest.mark.parametrize('uri', SAMPLE_URIS)
def test_check_roundtrip(uri: str) -> None:
    '''Check that a canonical URI can be parsed and then regurgitated successfully.'''
    assert str(URI.from_string(uri)) == uri


@pytest.mark.parametrize('uri', SAMPLE_URIS)
def test_check_equality(uri: str) -> None:
    '''Check that equality testing works.'''
    uri1 = URI.from_string(uri)
    uri2 = URI.from_string(uri)

    assert uri1 == uri2


def test_check_hash() -> None:
    '''Check that hashing works.'''
    assert isinstance(hash(URI.from_string(SAMPLE_URIS[0])), int)
