# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt domains.'''

from __future__ import annotations

import logging

from enum import CONTINUOUS, UNIQUE, Enum, verify
from time import sleep
from typing import TYPE_CHECKING, Any, ClassVar, Final, Literal, Self, cast, overload
from uuid import UUID

import libvirt

from .descriptors import ConfigAttributeProperty, ConfigElementProperty, MethodProperty
from .entity import LifecycleResult, RunnableEntity
from .entity_access import BaseEntityAccess, EntityAccess, EntityMap, NameMap, UUIDMap
from .exceptions import EntityNotRunning, InvalidOperation
from .stream import Stream
from ..util.match import MatchAlias

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .hypervisor import Hypervisor
    from .models.domain import DomainInfo

LOGGER: Final = logging.getLogger(__name__)


def _non_negative_integer(value: int, _instance: Any) -> None:
    if not isinstance(value, int):
        raise ValueError(f'{ value } is not a positive integer.')
    else:
        if value < 1:
            raise ValueError(f'{ value } is not a positive integer.')


def _currentCPUs_validator(value: int, instance: Domain) -> None:
    _non_negative_integer(value, instance)

    if value > instance.max_cpus:
        raise ValueError('Current CPU count may not exceed max CPU count.')


def _memory_validator(value: int, instance: Domain) -> None:
    _non_negative_integer(value, instance)

    if value > instance.max_memory:
        raise ValueError('Memory cannot exceed maxMemory value.')


def _currentMemory_validator(value: int, instance: Domain) -> None:
    _non_negative_integer(value, instance)

    if value > instance.memory:
        raise ValueError('Current memory cannot exceed memory value.')


@verify(UNIQUE)
@verify(CONTINUOUS)
class DomainState(Enum):
    '''Enumerable for domain states.'''
    UNKNOWN = -1
    NONE = libvirt.VIR_DOMAIN_NOSTATE
    RUNNING = libvirt.VIR_DOMAIN_RUNNING
    BLOCKED = libvirt.VIR_DOMAIN_BLOCKED
    PAUSED = libvirt.VIR_DOMAIN_PAUSED
    SHUTDOWN = libvirt.VIR_DOMAIN_SHUTDOWN
    SHUTOFF = libvirt.VIR_DOMAIN_SHUTOFF
    CRASHED = libvirt.VIR_DOMAIN_CRASHED
    PMSUSPEND = libvirt.VIR_DOMAIN_PMSUSPENDED

    def __str__(self: Self) -> str:
        match self:
            case DomainState.SHUTDOWN:
                return 'shutting down'
            case DomainState.SHUTOFF:
                return 'shut off'
            case DomainState.PMSUSPEND:
                return 'suspended by guest'

        return self.name.lower()


class Domain(RunnableEntity):
    '''Basic class encapsulating a libvirt domain.

       This is a wrapper around a libvirt.virDomain instance. It lacks
       some of the functionality provided by that class, but wraps most
       of the useful parts in a nicer, more Pythonic interface.'''
    MATCH_ALIASES: ClassVar = {
        'arch': MatchAlias(property='os_arch', desc='Match on the architecture of the domain.'),
        'autostart': MatchAlias(property='autostart', desc='Match on whether the domain is set to autostart or not.'),
        'current-snapshot': MatchAlias(property='has_current_snapshot', desc='Match on whether the domain has a current snapshot or not.'),
        'machine': MatchAlias(property='os_machine', desc='Match on the machine type of the domain.'),
        'managed-save': MatchAlias(property='has_managed_save', desc='Match on whether the domain has a managed save state or not.'),
        'name': MatchAlias(property='name', desc='Match on the name of the domain.'),
        'os-type': MatchAlias(property='os_type', desc='Match on the OS type of the domain.'),
        'persistent': MatchAlias(property='persistent', desc='Match on whether the domain is persistent or not.'),
        'state': MatchAlias(property='state', desc='Match on the current state of the domain.'),
    }

    genid: ConfigElementProperty[UUID] = ConfigElementProperty(
        doc='The generation ID of the domain.',
        path='./genid',
        type=UUID,
    )
    os_type: ConfigElementProperty[str] = ConfigElementProperty(
        doc='THe OS type of the domain.',
        path='./os/type',
        typ=str,
    )
    os_arch: ConfigAttributeProperty[str] = ConfigAttributeProperty(
        doc='The CPU architecture of the domain.',
        path='./os',
        attr='arch',
        typ=str,
    )
    os_machine: ConfigAttributeProperty[str] = ConfigAttributeProperty(
        doc='The machine type of the domain.',
        path='./os',
        attr='machine',
        typ=str,
    )
    emulator: ConfigElementProperty[str] = ConfigElementProperty(
        doc='The emulator used for the domain.',
        path='./devices/emulator',
        typ=str,
    )
    max_cpus: ConfigElementProperty[int] = ConfigElementProperty(
        doc='The maximum number of virtuual CPUs for the domain.',
        path='./vcpu',
        typ=int,
        validator=_non_negative_integer,
    )
    current_cpus: ConfigAttributeProperty[int] = ConfigAttributeProperty(
        doc='The current number of virtual CPUs attached to the domain.',
        path='./vcpu',
        attr='current',
        typ=int,
        fallback='maxCPUs',
        validator=_currentCPUs_validator,
    )
    max_memory: ConfigElementProperty[int] = ConfigElementProperty(
        doc='The maximum amount of memory that can be allocated to the domain.',
        path='./maxMemory',
        typ=int,
        units_to_bytes=True,
        validator=_non_negative_integer,
    )
    max_memory_slots: ConfigAttributeProperty[int] = ConfigAttributeProperty(
        doc='The number of memory slots in the domain.',
        path='./maxMemory',
        attr='slots',
        typ=int,
        validator=_non_negative_integer,
    )
    memory: ConfigElementProperty[int] = ConfigElementProperty(
        doc='The total memory allocated to the domain.',
        path='./memory',
        typ=int,
        fallback='maxMemory',
        units_to_bytes=True,
        validator=_memory_validator,
    )
    current_memory: ConfigElementProperty[int] = ConfigElementProperty(
        doc='The current memory in use by the domain, not including any reclaimed by a memory balloon.',
        path='./currentMemory',
        typ=int,
        fallback='memory',
        units_to_bytes=True,
        validator=_currentMemory_validator,
    )
    id: MethodProperty[int] = MethodProperty(
        doc='The libvirt ID of the domain. Only valid for running domains.',
        get='ID',
        type=int,
    )
    has_current_snapshot: MethodProperty[bool] = MethodProperty(
        doc='Whether or not the domain has a current snapshot.',
        get='hasCurrentSnapshot',
        type=bool,
    )
    has_managed_save: MethodProperty[bool] = MethodProperty(
        doc='Whether or not the domain has a managed save state.',
        get='hasManagedSaveImage',
        type=bool,
    )

    @overload
    def __init__(self: Self, entity: Domain, parent: None = None, /) -> None: ...

    @overload
    def __init__(self: Self, entity: libvirt.virDomain, parent: Hypervisor, /) -> None: ...

    def __init__(self: Self, entity: libvirt.virDomain | Domain, parent: Hypervisor | None = None, /) -> None:
        super().__init__(entity, parent)

    def __repr__(self: Self) -> str:
        if self.valid:
            return f'<fvirt.libvirt.Domain: name={ self.name }>'
        else:
            return '<fvirt.libvirt.Domain: INVALID>'

    @property
    def _wrapped_class(self: Self) -> Any:
        return libvirt.virDomain

    @property
    def _format_properties(self: Self) -> set[str]:
        return super()._format_properties | {
            'id',
        }

    @property
    def _define_method(self: Self) -> str:
        return 'define_domain'

    @property
    def _config_flags(self: Self) -> int:
        flags = 0

        if not self._hv.read_only:
            flags |= libvirt.VIR_DOMAIN_XML_SECURE

        return flags

    @property
    def _config_flags_inactive(self: Self) -> int:
        return cast(int, self._config_flags | libvirt.VIR_DOMAIN_XML_INACTIVE)

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

    def reset(self: Self) -> Literal[LifecycleResult.SUCCESS]:
        '''Attempt to reset the domain.

           If the domain is not running, raises fvirt.libvirt.EntityNotRunning.

           Exact behavior of a reset depends on the specific hypervisor
           driver, but this operation is generally a hard reset, similar
           to toggling the reset line on the processor.'''
        self._check_valid()

        if not self.running:
            raise EntityNotRunning

        LOGGER.info(f'Resetting domain: {repr(self)}')
        self._entity.reset()

        return LifecycleResult.SUCCESS

    def shutdown(
        self: Self,
        /, *,
        timeout: int | None = None,
        force: bool = False,
        idempotent: bool = False,
    ) -> LifecycleResult:
        '''Attempt to gracefully shut down the domain.

           If the domain is not running, do nothing and return the value
           of the idempotent parameter.

           If the domain is running, attempt to gracefully shut it down,
           returning True on success or False on failure.

           If timeout is a non-negative integer, it specifies a timeout
           in seconds that we should wait for the domain to shut down. If
           the timeout is exceeded and force is True, then the domain
           will be forcibly stopped (equivalent to calling the destroy()
           method). A timeout of less than 0 indicates that fvirt should
           use an arbitrary large timeout with longer polling periods.

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
                    tmcount = 60
                    interval = 5
                else:
                    tmcount = timeout
                    interval = 1
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

        LOGGER.info(f'Beginning shutdown of domain: {repr(self)}')
        self._entity.shutdown()

        while tmcount > 0:
            # The cast below is needed to convince type checkers that
            # self.running may not be True anymore at this point, since
            # they do not know that self._entity.shutdown() may result in
            # it's value changing.
            if not cast(bool, self.running):
                if mark_invalid:
                    self._valid = False

                break

            tmcount -= interval
            sleep(interval)

        if cast(bool, self.running):
            if force:
                LOGGER.warning(f'Failed to shut down domain: {repr(self)}')

                match self.destroy(idempotent=True):
                    case LifecycleResult.SUCCESS:
                        return LifecycleResult.FORCED
                    case LifecycleResult.NO_OPERATION:
                        self._valid = False
                        return LifecycleResult.SUCCESS

                raise RuntimeError
            elif timeout is None:
                return LifecycleResult.SUCCESS
            else:
                LOGGER.warning(f'Timed out waiting for shut down of domain: {repr(self)}')
                return LifecycleResult.TIMED_OUT
        else:
            LOGGER.info(f'Finished shutdown of domain: {repr(self)}')
            return LifecycleResult.SUCCESS

    def managed_save(self: Self, /, *, idempotent: bool = True) -> LifecycleResult:
        '''Suspend the domain and save it's state to disk.

           On the next start, this saved state will be used to restore
           the state of the domain.'''
        self._check_valid()

        if not self.running:
            if self.has_managed_save:
                if idempotent:
                    return LifecycleResult.SUCCESS
                else:
                    return LifecycleResult.NO_OPERATION
            else:
                raise EntityNotRunning

        if not self.persistent:
            raise InvalidOperation('Managed saves are only possible for persistent domains.')

        LOGGER.info(f'Saving state of domain: {repr(self)}')
        self._entity.managedSave(flags=0)

        return LifecycleResult.SUCCESS

    def console(self: Self, /, dev: str | None = None, *, force: bool = False, safe: bool = False) -> Stream:
        '''Get a Stream connected to the specified console device for the domain.

           Specifying a device of None will open the first console or serial device for the domain.'''
        self._check_valid()

        if not self.running:
            raise EntityNotRunning

        flags = 0

        if force:
            flags |= libvirt.VIR_DOMAIN_CONSOLE_FORCE

        if safe:
            flags |= libvirt.VIR_DOMAIN_CONSOLE_SAFE

        stream = Stream(self._hv, sparse=False, interactive=True)
        self._entity.openConsole(dev, stream.stream, flags)
        return stream

    @staticmethod
    def _get_template_info() -> tuple[type[DomainInfo], str] | None:
        from .models.domain import DomainInfo

        return (DomainInfo, 'domain.xml')


class Domains(BaseEntityAccess[Domain]):
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


class DomainsByName(NameMap[Domain], Domains):
    '''Immutabkle mapping returning domains on a Hypervisor based on their names.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByName'


class DomainsByUUID(UUIDMap[Domain], Domains):
    '''Immutabkle mapping returning domains on a Hypervisor based on their UUIDs.'''
    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByUUIDString'


class DomainsByID(EntityMap[Domain], Domains):
    '''Immutabkle mapping returning running domains on a Hypervisor based on their IDs.'''
    @property
    def _count_funcs(self: Self) -> Iterable[str]:
        return {'numOfDomains'}

    @property
    def _lookup_func(self: Self) -> str:
        return 'lookupByID'

    @staticmethod
    def _filter_entities(entities: Iterable) -> Iterable:
        return iter(x for x in entities if x.ID() > 0)

    def _get_key(self: Self, entity: Any) -> int:
        return cast(int, entity.ID())

    def _coerce_key(self: Self, key: Any) -> int:
        if not isinstance(key, int) or key < 1:
            raise KeyError(key)

        return key


class DomainAccess(EntityAccess[Domain], Domains):
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

    def get(self: Self, key: Any, /) -> Domain | None:
        '''Look up a domain by a general identifier.

           This tries, in order, looking up by ID, then by name, then
           by UUID. If it can't find a domain based on that key,
           it returns None.'''
        ret: Domain | None = None

        if isinstance(key, int):
            ret = self.by_id.get(key, None)
        elif isinstance(key, str) or isinstance(key, float):
            try:
                ret = self.by_id.get(int(key), None)
            except ValueError:
                pass

        if ret is None:
            ret = super().get(key)

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
]
