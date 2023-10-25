# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.uri'''

import pytest

from fvirt.libvirt.uri import DRIVER_INFO, LIBVIRT_DEFAULT_URI, URI, Driver, DriverFlag

# Definitions used below
CLIENT_ONLY_DRIVER = [x for x in Driver if DriverFlag.CLIENT_ONLY in DRIVER_INFO[x]][0].value
NON_SYSTEM_DRIVER = [x for x in Driver if DriverFlag.SYSTEM not in DRIVER_INFO[x]][0].value
SYSTEM_DRIVER = [x for x in Driver if DriverFlag.SYSTEM in DRIVER_INFO[x]][0].value
NON_SESSION_DRIVER = [x for x in Driver if DriverFlag.SESSION not in DRIVER_INFO[x]][0].value
NON_EMBED_DRIVER = [x for x in Driver if DriverFlag.EMBED not in DRIVER_INFO[x]][0].value
EMBED_DRIVER = [x for x in Driver if DriverFlag.EMBED in DRIVER_INFO[x]][0].value
NON_REMOTE_DRIVER = [x for x in Driver if DriverFlag.REMOTE not in DRIVER_INFO[x] and DriverFlag.SESSION in DRIVER_INFO[x]][0].value
NON_PATH_DRIVER = [x for x in Driver if DriverFlag.PATH not in DRIVER_INFO[x]][0].value

# An assortment of cannonical URIs used for the tests.
SAMPLE_URIS = (
    'openvz+ssh://root@example.com/system',
    'qemu:///system',
    'test:///default',
    'vbox+tcp://user@example.com:1234/session',
    'xen://example.com/system',
    'hyperv://example-hyperv.com/?transport=http',
    'ch:///session',
    'bhyve+ext://example.com/system?command=nc',
    'qemu:///embed?path=/foo',
    'esx://example.com/?transport=http&auto_answer=0',
)

# An assortment of known invalid URIs used for tests.
# Each of these should test _exactly_ one failure mode.
BAD_URIS = (
    ':///',  # No scheme
    'foo:///',  # Bogus driver
    'qemu+bar:///system',  # Bogus transport
    'qemu+unix+ssh://example.com/',  # Scheme with more than two components
    'test://example.com:0/',  # Invalid port number
    'test+ext:///defaults',  # Ext transport without command.
    'test+unix://root@example.com/',  # User with non-remote transport
    'test+unix://example.com/',  # Hostname with non-remote transport
    f'{ CLIENT_ONLY_DRIVER }+ssh://example.com/',  # Client-only driver with transport
    f'{ CLIENT_ONLY_DRIVER }:///',  # Client-only driver without host
    f'{ NON_SYSTEM_DRIVER }:///system',  # Using /system with non-system driver
    f'{ NON_SESSION_DRIVER }:///session',  # Using /session path with non-session driver
    f'{ NON_EMBED_DRIVER }:///embed?path=/foo',  # Using /embed path with non-embed driver
    f'{ EMBED_DRIVER }:///embed',  # Using /embed without path parameter
    f'{ NON_REMOTE_DRIVER }://example.com/session',  # Local-only driver with host
    f'{ NON_PATH_DRIVER }:///foo/bar',  # Using arbitrary path with driver that does not support it
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
    assert str(uri1) != uri2


def test_check_hash() -> None:
    '''Check that hashing works.'''
    assert isinstance(hash(URI.from_string(SAMPLE_URIS[0])), int)


def test_check_repr() -> None:
    '''Check that repr works.'''
    assert isinstance(repr(URI.from_string(SAMPLE_URIS[0])), str)


def test_check_default_uri() -> None:
    '''Check that the default URI constant evaluates to an empty string.'''
    assert str(LIBVIRT_DEFAULT_URI) == ''
