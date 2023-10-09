# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.uri'''

import pytest

from fvirt.libvirt.uri import CLIENT_ONLY_DRIVERS, SESSION_DRIVERS, SYSTEM_DRIVERS, URI

# Definitions used below
CLIENT_ONLY_DRIVER = list(CLIENT_ONLY_DRIVERS)[0]
SESSION_DRIVER = list(SESSION_DRIVERS)[0]
SYSTEM_DRIVER = list(SYSTEM_DRIVERS)[0]

# An assortment of cannonical URIs used for the tests.
SAMPLE_URIS = {
    'openvz+ssh://root@example.com/system',
    'qemu:///system',
    'test:///default',
    'vbox+tcp://user@example.com/session',
    'xen://example.com/system',
    'hyperv://example-hyperv.com/?transport=http',
    'ch:///session',
    'bhyve+ext://example.com/session?command=nc',
}

# An assortment of known invalid URIs used for tests.
# Each of these should test _exactly_ one failure mode.
BAD_URIS = {
    'foo:///',  # Bogus driver
    'qemu+bar:///system',  # Bogus transport
    'xen://example.com:0/',  # Invalid port number
    'test+ext:///defaults',  # Ext driver without command.
    f'{ CLIENT_ONLY_DRIVER.value }+ssh://example.com/',  # Client-only driver with transport
    f'{ CLIENT_ONLY_DRIVER.value }:///',  # Client-only driver without host
    f'{ SESSION_DRIVER }:///system',  # Using system with session driver
    f'{ SYSTEM_DRIVER }:///session',  # Using session with system driver
}


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
