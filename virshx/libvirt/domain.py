# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt domains.'''

from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING, Self, cast
from uuid import UUID

from lxml import etree

from .exceptions import InvalidDomain, InsufficientPrivileges

if TYPE_CHECKING:
    import libvirt

    from .hypervisor import Hypervisor


def update_element_text(tree: etree._Element, path: str, text: str) -> etree._Element:
    '''Update the text of the element at path in tree.

       Expects the requested element to exist.'''
    element = tree.find(path)

    if element is None:
        raise RuntimeError

    element.text = text

    return tree


def update_element_attribute(tree: etree._Element, path: str, attrib: str, value: str) -> etree._Element:
    '''Update the value of the attribute attrib of the element at path in tree.

       Expects the requested element to exist.'''
    element = tree.find(path)

    if element is None:
        raise RuntimeError

    element.set(attrib, value)

    return tree


class Domain:
    '''Basic class encapsulating a libvirt domain.

       This is a wrapper around a libvirt.virDomain instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.'''
    def __init__(self: Self, dom: libvirt.virDomain | Domain, conn: Hypervisor) -> None:
        if isinstance(dom, Domain):
            self._domain: libvirt.virDomain = dom._domain
        else:
            self._domain = dom

        self._conn = conn
        self._valid = True

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<virshx.libvirt.Domain: name={ self.name }>'
        else:
            return '<virshx.libvirt.Domain: INVALID>'

    @property
    def valid(self: Self) -> bool:
        '''Whether the domain is valid or not.

           Defaults to True on Domain instance creation.

           Will be set to false when the domain is shut down or destroyed
           if the domain is transient.

           If this is false, most calling most methods or accessing most
           properties will raise a virshex.libvirt.InvalidDomain error.'''
        return self._valid

    @property
    def configRaw(self: Self) -> str:
        '''The raw XML configuration of the domain.

           Writing to this property will attempt to redefine the domain
           with the specified config.

           For pre-parsed XML configuration, use the config property
           instead.'''
        if not self.valid:
            raise InvalidDomain

        flags = libvirt.VIR_DOMAIN_XML_INACTIVE

        if not self._conn.read_only:
            flags |= libvirt.VIR_DOMAIN_XML_SECURE

        return cast(str, self._domain.XMLDesc(flags))

    @configRaw.setter
    def configRaw(self: Self, config: str) -> None:
        '''Recreate the domain with the specified raw XML configuration.'''
        self._domain = self._conn.defineDomain(config)._domain

        self._valid = True

    @property
    def config(self: Self) -> etree._Element:
        '''The XML configuration of the domain as an lxml.etree.Element instnce.

           Writing to this property will attempt to redefine the domain
           with the specified config.

           For the raw XML as a string, use the rawConfig property.'''
        if not self.valid:
            raise InvalidDomain

        return etree.fromstring(self.configRaw)

    @config.setter
    def config(self: Self, config: etree._Element) -> None:
        '''Recreate the domain with the specified XML configuration.'''
        self.configRaw = etree.tostring(config, encoding='unicode')

        self._valid = True

    @property
    def running(self: Self) -> bool:
        '''Whether the domain is running or not.'''
        if not self.valid:
            return False

        return bool(self._domain.isActive())

    @property
    def persistent(self: Self) -> bool:
        '''Whether the domain is persistent or not.'''
        if not self.valid:
            return False

        return bool(self._domain.isPersistent())

    @property
    def name(self: Self) -> str:
        '''The name of the domain.'''
        if not self.valid:
            raise InvalidDomain

        return cast(str, self._domain.name())

    @name.setter
    def name(self: Self, name: str) -> None:
        if not isinstance(name, str):
            raise ValueError('Name must be a string.')

        if not self.valid:
            raise InvalidDomain

        if self._conn.read_only:
            raise InsufficientPrivileges

        self.config = update_element_text(self.config, './name', name)

    @property
    def uuid(self: Self) -> UUID:
        '''The UUID of the domain.'''
        if not self.valid:
            raise InvalidDomain

        return UUID(self._domain.UUIDString())

    @property
    def id(self: Self) -> int | None:
        '''The libvirt id of the domain, or None if it is not running.'''
        if not self.valid:
            raise InvalidDomain

        domid = self._domain.ID()

        if domid == -1:
            return None

        return cast(int, domid)

    @property
    def maxCPUs(self: Self) -> int:
        '''The maximum number of VCPUs for the domain.'''
        if not self.valid:
            raise InvalidDomain

        return cast(int, self._domain.maxVcpus())

    @maxCPUs.setter
    def maxCPUs(self: Self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError('Max CPU count should be a positive integer.')
        else:
            if value < 1:
                raise ValueError('Max CPU count should be a positive integer.')

        if not self.valid:
            raise InvalidDomain

        if self._conn.read_only:
            raise InsufficientPrivileges

        self.config = update_element_text(self.config, './vcpu', str(value))

    @property
    def currentCPUs(self: Self) -> int:
        '''The current number of VCPUs for the domain.'''
        if not self.valid:
            raise InvalidDomain

        element = self.config.find('./vcpu')

        if element is None:
            raise RuntimeError

        return int(element.get('current', self.maxCPUs))

    @currentCPUs.setter
    def currentCPUs(self: Self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError('Current CPU count should be a positive integer.')
        else:
            if value < 1:
                raise ValueError('Current CPU count should be a positive integer.')
            elif value > self.maxCPUs:
                raise ValueError('Current CPU count may not exceed max CPU count.')

        if not self.valid:
            raise InvalidDomain

        if self._conn.read_only:
            raise InsufficientPrivileges

        self.config = update_element_attribute(self.config, './vcpu', 'current', str(value))

    def start(self: Self) -> bool:
        '''Idempotently start the domain.

           If called on a domain that is already running, do nothing
           and return True.

           If called on a domain that is not running, attempt to start
           it, and return True if successful or False if unsuccessful.'''
        if not self.valid:
            raise InvalidDomain

        if self.running:
            return True

        try:
            self._domain.create()
        except libvirt.libvirtError:
            return False

        return True

    def shutdown(self: Self, timeout: int | None = None) -> bool:
        '''Idempotently attempt to gracefully shut down the domain.

           If the domain is not running, do nothing and return True.

           If the domain is running, attempt to gracefully shut it down,
           returning True on success or False on failure.

           If timeout is a non-negative integer, it specifies a timeout
           in seconds that we should wait for the domain to shut
           down. Exceeding the timeout will be treated as a failure to
           shut down the domain and return False.

           The timeout is polled roughly once per second using time.sleep().

           To forcibly shutdown ('destroy' in libvirt terms) the domain,
           use the destroy() method instead.

           If the domain is transient, the Domain instance will become
           invalid and most methods and property access will raise a
           virshex.libvirt.InvalidDomain exception.'''
        if not self.valid:
            raise InvalidDomain

        if timeout is None:
            tmcount = 0
        else:
            if isinstance(timeout, int):
                if timeout < 0:
                    tmcount = 0
                else:
                    tmcount = timeout
            else:
                raise ValueError(f'Invalid timeout specified: { timeout }.')

        if not self.running:
            return True

        mark_invalid = False

        if not self.persistent:
            mark_invalid = True

        try:
            self._domain.shutdown()
        except libvirt.libvirtError:
            return False

        while tmcount > 0:
            # The cast below is needed to convince type checkers that
            # self.running may not be True anymore at this point, since
            # they do not know that self._domain.shutdown() may result in
            # it's value changing.
            if not cast(bool, self.running):
                if mark_invalid:
                    self._valid = False

                break

            tmcount -= 1
            sleep(1)

        return self.running

    def destroy(self: Self) -> bool:
        '''Idempotently attempt to forcibly shut down the domain.

           If the domain is not running, do nothing and return True.

           If the domain is running, attempt to forcibly shut it down,
           returning True on success or False on failure.

           The timeout is polled roughly once per second using time.sleep().

           To gracefully shut down the domain instead use the shutdown()
           method.

           If the domain is transient, the Domain instance will become
           invalid and most methods and property access will raise a
           virshex.libvirt.InvalidDomain exception.'''
        if not self.valid:
            raise InvalidDomain

        if not self.running:
            return True

        mark_invalid = False

        if not self.persistent:
            mark_invalid = True

        try:
            self._domain.destroy()
        except libvirt.libvirtError:
            return False

        if mark_invalid:
            self._valid = False

        return True

    def applyXSLT(self: Self, xslt: etree.XSLT) -> None:
        '''Apply the given XSLT object to the domain's configuration.

           This handles reading the config, applying the transformation,
           and then saving the config, all aas one operation.'''
        self.configRaw = str(xslt(self.config))
