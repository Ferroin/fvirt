# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt hypervisor connections.'''

from __future__ import annotations

from typing import Self
from types import TracebackType
from uuid import UUID

import libvirt

from ..common import name_match
from .domain import Domain
from .exceptions import NotConnected, InvalidConfig, InsufficientPrivileges


class Hypervisor:
    '''Basic class encapsulating a hypervisor connection.

       This is a wrapper around a libvirt.virConnect instance that
       provides a bunch of extra convenience functionality, such as a
       proper context manager interface and the ability to list _all_
       domains.

       When converting to a boolean, Hypervisor instances are treated as
       false if they are not connected, and true if they have at least
       one active connection.'''
    def __init__(self: Self, hvuri: str, read_only: bool = False) -> None:
        self._uri = str(hvuri)
        self._read_only = bool(read_only)
        self._connection: libvirt.virConnect | None = None
        self._conn_count = 0

    def __repr__(self: Self) -> str:
        return f'<virshx.libvirt.Hypervisor: uri={ self._uri }, ro={ self._read_only }, conns={ self._conn_count }>'

    def __bool__(self: Self) -> bool:
        return self._conn_count > 0

    def __del__(self: Self) -> None:
        if self._connection is not None and self._conn_count > 0:
            self._connection.close()
            self._connection = None

    def __enter__(self: Self) -> Self:
        return self.open()

    def __exit__(self: Self, _exc_type: type | None, _exc_value: BaseException | None, _traceback: TracebackType | None) -> None:
        self.close()

    @property
    def read_only(self: Self) -> bool:
        return self._read_only

    def open(self: Self) -> Self:
        '''Open the connection represented by this hypervisor instance.

           In almost all cases, the context manager interface is preferred.'''
        if self._connection is None:
            try:
                if self._read_only:
                    self._connection = libvirt.openReadOnly(self._uri)
                else:
                    self._connection = libvirt.open(self._uri)
            except libvirt.libvirtError as e:
                raise e

            self._conn_count += 1
        else:
            if self._conn_count == 0:
                raise RuntimeError
            else:
                self._conn_count += 1

        return self

    def close(self: Self) -> None:
        '''Close any open connection represented by this hypervisor instance.

           Open connections will be cleaned up automatically when a
           Hypervisor instance is destroyed, so you should usually not
           need to call this method directly.'''
        if self._connection is not None and self._conn_count < 2:
            self._connection.close()
            self._connection = None

        self._conn_count -= 1

        if self._conn_count < 0:
            self._conn_count = 0

    def getDomainByName(self: Self, name: str, /) -> Domain | None:
        '''Get a domain by name.

           Returns None if no domain matches.

           This requires an exact match.'''
        if self._connection is None:
            raise NotConnected

        if not isinstance(name, str):
            raise ValueError('Domain name must be a string.')

        match self._connection.lookupByName(name):
            case None:
                return None
            case domain:
                return Domain(domain, self)

    def getDomainByID(self: Self, domid: int, /) -> Domain | None:
        '''Get a domain by ID.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Returns None if no domain matches.'''
        if self._connection is None:
            raise NotConnected

        if not isinstance(domid, int):
            raise ValueError('Domain ID must be an integer.')

        if domid < 0:
            raise ValueError('Domain ID must not be negative.')

        match self._connection.lookupByID(domid):
            case None:
                return None
            case domain:
                return Domain(domain, self)

    def getDomainByUUID(self: Self, domuuid: str | bytes | UUID, /) -> Domain | None:
        '''Get a domain by UUID.

           Accepts either a UUID string, a big-endian bytes object
           representing the raw bytes of the UUID, or a pre-constructed
           UUID object.

           Strings and bytes are parsed as UUIDs using the uuid.UUID
           class from the Python standard library, so any string format
           accepted by the uuid.UUID constructor is also accepted by
           this function.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Returns None if no domain matches.'''
        if self._connection is None:
            raise NotConnected

        match domuuid:
            case str() as u:
                domuuid = UUID(u)
            case bytes() as u:
                domuuid = UUID(bytes=u)
            case UUID():
                pass
            case _:
                raise ValueError(f'Unsupported type for UUID: { type(domuuid) }')

        match self._connection.lookupByUUID(str(domuuid)):
            case None:
                return None
            case domain:
                return Domain(domain, self)

    def getActiveDomains(self: Self) -> list[Domain]:
        '''Get a list of active domains.

           This takes care of resolving domain IDs to actual domains.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Returns an empty list if no domains are active.'''
        if self._connection is None:
            raise NotConnected

        domids: list[int] | None = self._connection.listDomainsID()

        if domids is None:
            return []
        elif all(isinstance(i, int) for i in domids):
            ret = []

            for domid in domids:
                dom = self.getDomainByID(domid)

                if dom is not None:
                    ret.append(Domain(dom, self))

            return ret
        else:
            raise RuntimeError

    def getInactiveDomains(self: Self) -> list[Domain]:
        '''Get a list of inactive domains.

           This takes care of resolving domain names to actual domains.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Returns an empty list if there are no inactive domains.'''
        if self._connection is None:
            raise NotConnected

        domnames: list[str] | None = self._connection.listListDefinedDomains()

        if domnames is None:
            return []
        elif all(isinstance(i, str) for i in domnames):
            ret = []

            for domname in domnames:
                dom = self.getDomainByName(domname)

                if dom is not None:
                    ret.append(Domain(dom, self))

            return ret
        else:
            raise RuntimeError

    def getDomains(self: Self) -> list[Domain]:
        '''Get a list of all domains.

           This takes care of resolving domain names and IDs to actual domains.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Returns an empty list if there are no inactive domains.'''
        return self.getActiveDomains() + self.getInactiveDomains()

    def getDomainsByName(self: Self, name_pattern: str) -> list[Domain]:
        '''Get a list of domains whose names match name_pattern.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Returns an empty list if there are no matching domains.'''
        domains = self.getDomains()

        ret = []

        for domain in domains:
            if name_match(domain.name, name_pattern):
                ret.append(Domain(domain, self))

        return ret

    def defineDomain(self: Self, config: str) -> Domain:
        '''Define a domain from an XML config string.

           Raises virshx.libvirt.NotConnected if called on a Hypervisor
           instance that is not connected.

           Raises virshx.libvirt.InvalidConfig if config is not a valid
           libvirt domain configuration.

           Returns a Domain instance for the defined domain on success.'''
        if self._read_only:
            raise InsufficientPrivileges

        if self._connection is None:
            raise NotConnected

        try:
            dom = self._connection.defineXMLFlags(config, 0)
        except libvirt.libvirtError:
            raise InvalidConfig

        return Domain(dom, self)
