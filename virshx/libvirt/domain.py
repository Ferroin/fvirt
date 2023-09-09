# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt domains.'''

from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING, Self, cast

import libvirt

from .entity import ConfigurableEntity, RunnableEntity, ConfigElementProperty, ConfigAttributeProperty

if TYPE_CHECKING:
    from .hypervisor import Hypervisor


def _non_negative_integer(value: int, _instance: Domain) -> None:
    if not isinstance(value, int):
        raise ValueError(f'{ value } is not a positive integer.')
    else:
        if value < 1:
            raise ValueError(f'{ value } is not a positive integer.')


def _currentCPUs_validator(value: int, instance: Domain) -> None:
    _non_negative_integer(value, instance)

    if value > instance.maxCPUs:
        raise ValueError('Current CPU count may not exceed max CPU count.')


def _memory_validator(value: int, instance: Domain) -> None:
    _non_negative_integer(value, instance)

    if value > instance.maxMemory:
        raise ValueError('Memory cannot exceed maxMemory value.')


def _currentMemory_validator(value: int, instance: Domain) -> None:
    _non_negative_integer(value, instance)

    if value > instance.memory:
        raise ValueError('Current memory cannot exceed memory value.')


class Domain(ConfigurableEntity, RunnableEntity):
    '''Basic class encapsulating a libvirt domain.

       This is a wrapper around a libvirt.virDomain instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.'''
    maxCPUs: ConfigElementProperty[int] = ConfigElementProperty(
        path='./vcpu',
        typ=int,
        validator=_non_negative_integer,
    )
    currentCPUs: ConfigAttributeProperty[int] = ConfigAttributeProperty(
        path='./vcpu',
        attrib='current',
        typ=int,
        fallback='maxCPUs',
        validator=_currentCPUs_validator,
    )
    maxMemory: ConfigElementProperty[int] = ConfigElementProperty(
        path='./maxMemory',
        typ=int,
        units_to_bytes=True,
        validator=_non_negative_integer,
    )
    maxMemorySlots: ConfigAttributeProperty[int] = ConfigAttributeProperty(
        path='./maxMemory',
        attrib='slots',
        typ=int,
        validator=_non_negative_integer,
    )
    memory: ConfigElementProperty[int] = ConfigElementProperty(
        path='./memory',
        typ=int,
        fallback='maxMemory',
        units_to_bytes=True,
        validator=_memory_validator,
    )
    currentMemory: ConfigElementProperty[int] = ConfigElementProperty(
        path='./currentMemory',
        typ=int,
        fallback='memory',
        units_to_bytes=True,
        validator=_currentMemory_validator,
    )

    def __init__(self: Self, dom: libvirt.virDomain | Domain, conn: Hypervisor) -> None:
        if isinstance(dom, Domain):
            dom = dom._entity

        super().__init__(dom, conn)

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<virshx.libvirt.Domain: name={ self.name }>'
        else:
            return '<virshx.libvirt.Domain: INVALID>'

    @property
    def _format_properties(self: Self) -> set[str]:
        return super()._format_properties | {
            'id',
            'maxCPUs',
            'currentCPUs',
        }

    @property
    def _define_method(self: Self) -> str:
        return 'defineDomain'

    @property
    def _config_flags(self: Self) -> int:
        flags: int = libvirt.VIR_DOMAIN_XML_INACTIVE

        if not self._conn.read_only:
            flags |= libvirt.VIR_DOMAIN_XML_SECURE

        return flags

    @property
    def id(self: Self) -> int | None:
        '''The libvirt id of the domain.

           A value of -1 is returned if the domain is not running.'''
        self._check_valid()

        domid = self._entity.ID()

        return cast(int, domid)

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
        self._check_valid()

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
            self._entity.shutdown()
        except libvirt.libvirtError:
            return False

        while tmcount > 0:
            # The cast below is needed to convince type checkers that
            # self.running may not be True anymore at this point, since
            # they do not know that self._entity.shutdown() may result in
            # it's value changing.
            if not cast(bool, self.running):
                if mark_invalid:
                    self._valid = False

                break

            tmcount -= 1
            sleep(1)

        return not self.running


__all__ = [
    'Domain',
]
