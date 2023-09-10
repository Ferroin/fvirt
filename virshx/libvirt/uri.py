# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Classes and constants for working with libvirt URIs.'''

from __future__ import annotations

from enum import Enum
from typing import Self, Type
from urllib.parse import quote, urlparse, parse_qs

from frozendict import frozendict


class Driver(Enum):
    '''Recognized drivers for libvirt URIs.'''
    BHYVE = 'bhyve'
    CLOUD_HYPERVISOR = 'ch'
    HYPERV = 'hyperv'
    LXC = 'lxc'
    OPENVZ = 'openvz'
    QEMU = 'qemu'
    TEST = 'test'
    VIRTUALBOX = 'vbox'
    VIRTUOZZO = 'vz'
    VMWARE_ESX = 'esx'
    VMWARE_FUSION = 'vmwarefusion'
    VMWARE_GSX = 'gsx'
    VMWARE_PLAYER = 'vmwareplayer'
    VMWARE_VPX = 'vpx'
    VMWARE_WORKSTATION = 'vmwarews'
    XEN = 'xen'

    KVM = 'qemu'
    HVF = 'qemu'


SESSION_DRIVERS = frozenset({
    Driver.CLOUD_HYPERVISOR,
    Driver.LXC,
    Driver.QEMU,
    Driver.VIRTUALBOX,
    Driver.VMWARE_FUSION,
    Driver.VMWARE_PLAYER,
    Driver.VMWARE_WORKSTATION,
})

SYSTEM_DRIVERS = frozenset({
    Driver.BHYVE,
    Driver.LXC,
    Driver.OPENVZ,
    Driver.QEMU,
    Driver.VIRTUOZZO,
    Driver.XEN,
})

CLIENT_ONLY_DRIVERS = frozenset({
    Driver.HYPERV,
    Driver.VMWARE_ESX,
    Driver.VMWARE_GSX,
    Driver.VMWARE_VPX,
})


class Transport(Enum):
    '''Recognized transports for libvirt URIs.'''
    EXTERNAL = 'ext'
    LIBSSH2 = 'libssh2'
    LIBSSH = 'libssh'
    SSH = 'ssh'
    TCP = 'tcp'
    TLS = ''
    UNIX = 'unix'

    LOCAL = 'unix'


class URI:
    '''A class representing a libvirt URI.'''
    __slots__ = [
        '__weakref__',
        '__driver',
        '__transport',
        '__user',
        '__host',
        '__port',
        '__path',
        '__parameters',
    ]

    def __init__(
            self: Self,
            /, *,
            driver: Driver | None = None,
            transport: Transport | None = None,
            user: str | None = None,
            host: str | None = None,
            port: int | None = None,
            path: str | None = None,
            parameters: dict[str, str] = dict(),
            ) -> None:
        self.__driver = driver
        self.__transport = transport
        self.__user = user
        self.__host = host
        self.__port = port
        self.__path = path
        self.__parameters = frozendict(parameters)

        if path == 'session' and driver not in SESSION_DRIVERS:
            raise ValueError('Driver does not support /session paths.')
        elif path == 'system' and driver not in SYSTEM_DRIVERS:
            raise ValueError('Driver does not support /system paths.')
        elif transport is not None and driver in CLIENT_ONLY_DRIVERS:
            raise ValueError('Transport must be None for client only drivers.')
        elif host is None and driver in CLIENT_ONLY_DRIVERS:
            raise ValueError('Host name must be specified with client-only drivers.')
        elif transport is Transport.EXTERNAL and 'command' not in parameters:
            raise ValueError('External transport requires a command to be specified in the URI parameters.')
        elif transport not in {Transport.SSH, Transport.LIBSSH, Transport.LIBSSH2} and user is not None:
            raise ValueError('User name is only supported for SSH transports.')
        elif port is not None and port not in range(1, 65536):
            raise ValueError('Invalid port number.')

        if self.__driver is None:
            self.__transport = None
            self.__host = None
            self.__path = None
            self.__parameters = frozendict()

        if self.__host is None:
            self.__user = None
            self.__port = None

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.URI driver={ self.driver } transport={ self.transport } user={ self.user } host={ self.host } ' + \
               f'port={ self.port } path={ self.path } parameters={ dict(self.parameters) }>'

    def __str__(self: Self) -> str:
        if self.driver is None:
            return ''

        uri = f'{ self.driver.value }'

        if self.transport is not None and self.transport.value:
            if self.transport is Transport.UNIX and self.host is None:
                uri = f'{ uri }://'
            else:
                uri = f'{ uri }+{ self.transport.value }://'

        if self.user is not None:
            uri = f'{ uri }{ self.user }@'

        if self.host is not None:
            uri = f'{ uri }{ self.host }'

        if self.port is not None:
            uri = f'{ uri }:{ self.port }'

        if self.path is not None:
            uri = f'{ uri }{ quote(self.path) }'
        else:
            uri = f'{ uri }/'

        first = True
        for key, value in self.parameters.items():
            if first:
                uri = f'{ uri }?{ key }={ quote(value, safe="") }'
                first = False
            else:
                uri = f'{ uri }&{ key }={ quote(value, safe="") } '

        return uri

    @property
    def driver(self: Self) -> Driver | None:
        '''The driver for this URI.

           If this value is None, then the default libvirt URI will
           be used, and most other properties will also show a value
           of None.'''
        return self.__driver

    @property
    def transport(self: Self) -> Transport | None:
        '''The transport for this URI.

           The meaning of a value of None is dependent on the value of
           the host property.

           If host is None, then the URI is local, and a value of None
           for transport is identical to a value of Transport.LOCAL.

           If host is not None, then the URI is remote, and a value of
           None for transport either means to use the driver-specific
           transport if using a client-only driver, or to use libvirt's
           TLS-encrypted network transport if using a regular driver.'''
        return self.__transport

    @property
    def user(self: Self) -> str | None:
        '''THe user name for this URI.

           A value of None is the same as an empty string.'''
        return self.__user

    @property
    def host(self: Self) -> str | None:
        '''The host name to connect to for this URI.

           A value of None indicates a local URI.'''
        return self.__host

    @property
    def port(self: Self) -> int | None:
        '''The port number for this URI.

           A value of None means to use the default.'''
        return self.__port

    @property
    def path(self: Self) -> str | None:
        '''The path for this URI.

           A value of None is the same as an empty string.

           Most drivers only support one or both of `session` or `system`.'''
        return self.__path

    @property
    def parameters(self: Self) -> frozendict[str, str]:
        '''An immutable mapping of URI parameters.

           Most drivers do not support any URI parameters.'''
        return self.__parameters

    @classmethod
    def from_string(cls: Type[URI], uri: str) -> URI:
        '''Construct a URI instance from a URI string.'''
        if not uri:
            return cls()

        urlparts = urlparse(uri, allow_fragments=False)

        if not urlparts.scheme:
            raise ValueError('No scheme specified for URI.')

        match urlparts.scheme.split('+'):
            case [str() as d1]:
                driver = Driver(d1)
                if urlparts.hostname is None:
                    transport = Transport.UNIX
                else:
                    transport = Transport('')
            case [str() as d2, str() as t1]:
                driver = Driver(d2)
                transport = Transport(t1)
            case _:
                raise ValueError('Invalid URI scheme.')

        if urlparts.hostname is None and transport is Transport(''):
            transport = Transport.UNIX

        params = {k: v[0] for k, v in parse_qs(urlparts.query, keep_blank_values=False, strict_parsing=True).items()}

        return cls(
            driver=driver,
            transport=transport,
            user=urlparts.username,
            host=urlparts.hostname,
            port=urlparts.port,
            path=urlparts.path or None,
            parameters=params,
        )


LIBVIRT_DEFAULT_URI = URI()


__all__ = [
    'Driver',
    'SESSION_DRIVERS',
    'SYSTEM_DRIVERS',
    'CLIENT_ONLY_DRIVERS',
    'Transport',
    'URI',
    'LIBVIRT_DEFAULT_URI',
]
