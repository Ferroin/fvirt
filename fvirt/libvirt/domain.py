# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt domains.'''

from __future__ import annotations

from enum import CONTINUOUS, UNIQUE, Enum, verify
from time import sleep
from typing import TYPE_CHECKING, Any, Literal, Self, cast
from uuid import UUID

import libvirt

from .entity import ConfigAttributeProperty, ConfigElementProperty, ConfigurableEntity, LifecycleResult, RunnableEntity
from .entity_access import BaseEntityAccess, EntityAccess, EntityMap, NameMap, UUIDMap
from .exceptions import EntityNotRunning, InvalidOperation
from ..util.match import MatchAlias

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .hypervisor import Hypervisor


MATCH_ALIASES = {
    'arch': MatchAlias(property='osArch', desc='Match on the architecture of the domain.'),
    'autostart': MatchAlias(property='autostart', desc='Match on whether the domain is set to autostart or not.'),
    'currentSnapshot': MatchAlias(property='hasCurrentSnapshot', desc='Match on whether the domain has a current snapshot or not.'),
    'machine': MatchAlias(property='osMachine', desc='Match on the machine type of the domain.'),
    'managedSave': MatchAlias(property='hasManagedSave', desc='Match on whether the domain has a managed save state or not.'),
    'name': MatchAlias(property='name', desc='Match on the name of the domain.'),
    'osType': MatchAlias(property='osType', desc='Match on the OS type of the domain.'),
    'persistent': MatchAlias(property='persistent', desc='Match on whether the domain is persistent or not.'),
    'state': MatchAlias(property='state', desc='Match on the current state of the domain.'),
}


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


@verify(UNIQUE)
@verify(CONTINUOUS)
class DomainState(Enum):
    '''Enumerable for domain states.

       This is manually copied from virDomainState in the libvirt C API
       because the libvirt Python modules neglect to expose it for some
       reason despite returning raw values for domain states.'''
    NONE = 0x0
    RUNNING = 0x1
    BLOCKED = 0x2
    PAUSED = 0x3
    SHUTDOWN = 0x4
    SHUTOFF = 0x5
    CRASHED = 0x6
    PMSUSPEND = 0x7
    UNKNOWN = 0x8

    def __str__(self: Self) -> str:
        match self:
            case DomainState.SHUTDOWN:
                return 'shutting down'
            case DomainState.SHUTOFF:
                return 'shut off'
            case DomainState.PMSUSPEND:
                return 'suspended by guest'

        return self.name.lower()


class Domain(ConfigurableEntity, RunnableEntity):
    '''Basic class encapsulating a libvirt domain.

       This is a wrapper around a libvirt.virDomain instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.'''
    genid: ConfigElementProperty[UUID] = ConfigElementProperty(
        path='./genid/text()[1]',
        typ=UUID,
    )
    osType: ConfigElementProperty[str] = ConfigElementProperty(
        path='./os/type/text()[1]',
        typ=str,
    )
    osArch: ConfigAttributeProperty[str] = ConfigAttributeProperty(
        path='./os',
        attrib='arch',
        typ=str,
    )
    osMachine: ConfigAttributeProperty[str] = ConfigAttributeProperty(
        path='./os',
        attrib='machine',
        typ=str,
    )
    emulator: ConfigElementProperty[str] = ConfigElementProperty(
        path='./devices/emulator/text()[1]',
        typ=str,
    )
    maxCPUs: ConfigElementProperty[int] = ConfigElementProperty(
        path='./vcpu/text()[1]',
        typ=int,
        validator=_non_negative_integer,
    )
    currentCPUs: ConfigAttributeProperty[int] = ConfigAttributeProperty(
        path='./vcpu/text()[1]',
        attrib='current',
        typ=int,
        fallback='maxCPUs',
        validator=_currentCPUs_validator,
    )
    maxMemory: ConfigElementProperty[int] = ConfigElementProperty(
        path='./maxMemory/text()[1]',
        typ=int,
        units_to_bytes=True,
        validator=_non_negative_integer,
    )
    maxMemorySlots: ConfigAttributeProperty[int] = ConfigAttributeProperty(
        path='./maxMemory/text()[1]',
        attrib='slots',
        typ=int,
        validator=_non_negative_integer,
    )
    memory: ConfigElementProperty[int] = ConfigElementProperty(
        path='./memory/text()[1]',
        typ=int,
        fallback='maxMemory',
        units_to_bytes=True,
        validator=_memory_validator,
    )
    currentMemory: ConfigElementProperty[int] = ConfigElementProperty(
        path='./currentMemory/text()[1]',
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
            return f'<fvirt.libvirt.Domain: name={ self.name }>'
        else:
            return '<fvirt.libvirt.Domain: INVALID>'

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

        if not self.__conn.read_only:
            flags |= libvirt.VIR_DOMAIN_XML_SECURE

        return flags

    @property
    def id(self: Self) -> int | None:
        '''The libvirt id of the domain.

           A value of -1 is returned if the domain is not running.'''
        self._check_valid()

        domid = self._entity.ID()

        return cast(int, domid)

    @property
    def hasCurrentSnapshot(self: Self) -> bool:
        '''Whether or not the domain has a current snapshot.'''
        self._check_valid()

        return bool(self._entity.hasCurrentSnapshot())

    @property
    def hasManagedSave(self: Self) -> bool:
        '''Whether or not the domain has a managed save state.'''
        self._check_valid()

        return bool(self._entity.hasManagedSaveImage())

    @property
    def state(self: Self) -> DomainState:
        '''The current state of the domain.'''
        self._check_valid()

        intstate = self._entity.state()[0]

        try:
            state = DomainState(intstate)
        except ValueError:
            state = DomainState.UNKNOWN

        return state

    @property
    def title(self: Self) -> str:
        '''The title of the domain.

           This is an optional bit of metadata describing the domain.'''
        self._check_valid()

        match self.config.xpath('/domain/title/text()[1]', smart_strings=False):
            case []:
                return ''
            case [str() as ret]:
                return ret
            case _:
                raise RuntimeError

    def reset(self: Self) -> Literal[LifecycleResult.SUCCESS, LifecycleResult.FAILURE]:
        '''Attempt to reset the domain.

           If the domain is not running, raises fvirt.libvirt.EntityNotRunning.

           Exact behavior of a reset depends on the specific hypervisor
           driver, but this operation is generally a hard reset, similar
           to toggling the reset line on the processor.'''
        self._check_valid()

        if not self.running:
            raise EntityNotRunning

        try:
            self._entity.reset()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def shutdown(self: Self, /, *, timeout: int | None = None, force: bool = False, idempotent: bool = False) -> LifecycleResult:
        '''Attempt to gracefully shut down the domain.

           If the domain is not running, do nothing and return the value
           of the idempotent parameter.

           If the domain is running, attempt to gracefully shut it down,
           returning True on success or False on failure.

           If timeout is a non-negative integer, it specifies a timeout
           in seconds that we should wait for the domain to shut down. If
           the timeout is exceeded and force is True, then the domain
           will be forcibly stopped (equivalent to calling the destroy()
           method) and True will be returned if that succeeds. If
           the timeout is exceeded and force is False (the default),
           a fvirt.libvirt.TimedOut exception will be raised.

           The timeout is polled roughly once per second using time.sleep().

           To forcibly shutdown ('destroy' in libvirt terms) the domain,
           use the destroy() method instead.

           If the domain is transient, the Domain instance will become
           invalid and most methods and property access will raise a
           fvirt.libvirt.InvalidDomain exception.'''
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

        if not self.running or not self.valid:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.NO_OPERATION

        mark_invalid = False

        if not self.persistent:
            mark_invalid = True

        try:
            self._entity.shutdown()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        while tmcount > 0:
            # The cast below is needed to convince type checkers that
            # self.running may not be True anymore at this point, since
            # they do not know that self._entity.shutdown() may result in
            # it's value changing.
            if not cast(bool, self.running):
                if mark_invalid:
                    self.__valid = False

                break

            tmcount -= 1
            sleep(1)

        if cast(bool, self.running):
            if force:
                match self.destroy(idempotent=True):
                    case LifecycleResult.SUCCESS:
                        return LifecycleResult.FORCED
                    case LifecycleResult.FAILURE:
                        return LifecycleResult.FAILURE
                    case LifecycleResult.NO_OPERATION:
                        self.__valid = False
                        return LifecycleResult.SUCCESS

                raise RuntimeError
            else:
                return LifecycleResult.TIMED_OUT
        else:
            return LifecycleResult.SUCCESS

    def managedSave(self: Self, idempotent: bool = True) -> LifecycleResult:
        '''Suspend the domain and save it's state to disk.

           On the next start, this saved state will be used to restore
           the state of the domain.'''
        self._check_valid()

        if not self.running:
            if self.hasManagedSave:
                if idempotent:
                    return LifecycleResult.NO_OPERATION
                else:
                    return LifecycleResult.FAILURE
            else:
                raise EntityNotRunning

        if not self.persistent:
            raise InvalidOperation('Managed saves are only possible for persistent domains.')

        try:
            self._entity.managedSave(flags=0)
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS


class Domains(BaseEntityAccess):
    '''Domain access mixin for Entity access protocol.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfDomains', 'numOfDefinedDomains'}

    @property
    def _list_func(self: Self) -> str:
        return 'listAllDomains'

    @property
    def _entity_class(self: Self) -> type:
        return Domain


class DomainsByName(NameMap, Domains):
    '''Immutabkle mapping returning domains on a Hypervisor based on their names.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByName'


class DomainsByUUID(UUIDMap, Domains):
    '''Immutabkle mapping returning domains on a Hypervisor based on their UUIDs.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByUUIDString'


class DomainsByID(EntityMap, Domains):
    '''Immutabkle mapping returning running domains on a Hypervisor based on their IDs.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfDomains'}

    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByID'

    def _get_key(self: Self, entity: Any) -> int:
        return cast(int, entity.ID())

    def _coerce_key(self: Self, key: Any) -> int:
        if not isinstance(key, int):
            raise KeyError(key)

        return key


class DomainAccess(EntityAccess, Domains):
    '''Class used for accessing domains on a Hypervisor.

       DomainAccess instances are iterable, returning the domains on
       the Hyopervisor in the order that libvirt returns them.

       DomainAccess instances are also sized, with len(instance) returning
       the total number of domains on the Hypervisor.'''
    def __init__(self: Self, parent: Hypervisor) -> None:
        self.__by_name = DomainsByName(parent)
        self.__by_uuid = DomainsByUUID(parent)
        self.__by_id = DomainsByID(parent)
        super().__init__(parent)

    def get(self: Self, key: str) -> Domain | None:
        '''Look up a domain by a general identifier.

           This tries, in order, looking up by name, then by UUID,
           then by ID. If it can't find a domain based on that key,
           it returns None.'''
        ret = cast(Domain | None, super().get(key))

        if ret is None:
            try:
                ID = int(key)
            except ValueError:
                pass
            else:
                ret = self.by_id.get(ID, None)

        return ret

    @property
    def by_name(self: Self) -> DomainsByName:
        '''Mapping access to domains by name.'''
        return self.__by_name

    @property
    def by_uuid(self: Self) -> DomainsByUUID:
        '''Mapping access to domains by UUID.'''
        return self.__by_uuid

    @property
    def by_id(self: Self) -> DomainsByID:
        '''Mapping access to domains by ID.'''
        return self.__by_id


__all__ = [
    'Domain',
    'DomainState',
    'MATCH_ALIASES',
]
