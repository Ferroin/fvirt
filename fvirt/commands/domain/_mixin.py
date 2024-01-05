# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixin for Domain related commands.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Self, Type

from .._base.objects import DisplayProperty, ObjectMixin
from .._base.tables import color_bool, color_optional
from .._base.terminal import get_terminal
from ...libvirt.domain import Domain, DomainState

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def color_state(state: DomainState) -> str:
    '''Apply colors to a domain state.'''
    TERM = get_terminal()

    match state:
        case d if d in {DomainState.RUNNING}:
            return TERM.bright_green_on_black(str(state))
        case d if d in {DomainState.CRASHED, DomainState.BLOCKED, DomainState.NONE}:
            return TERM.bright_red_on_black(str(state))
        case d if d in {DomainState.PAUSED}:
            return TERM.bright_yellow_on_black(str(state))
        case d if d in {DomainState.PMSUSPEND}:
            return TERM.bright_blue_on_black(str(state))
        case _:
            return str(state)

    raise RuntimeError  # Needed because mypy thinks the above case statement is non-exhaustive.


def format_id(value: int) -> str:
    '''Format a domain ID.'''
    if value == -1:
        return '-'
    else:
        return str(value)


_DISPLAY_PROPERTIES: Final = {
    'name': DisplayProperty(
        title='Name',
        name='Name',
        prop='name'
    ),
    'uuid': DisplayProperty(
        title='UUID',
        name='UUID',
        prop='uuid',
    ),
    'genid': DisplayProperty(
        title='GenID',
        name='Generation ID',
        prop='genid',
        color=color_optional,
    ),
    'id': DisplayProperty(
        title='ID',
        name='Domain ID',
        prop='id',
        right_align=True,
        color=format_id,
    ),
    'state': DisplayProperty(
        title='State',
        name='State',
        prop='state',
        color=color_state,
    ),
    'persistent': DisplayProperty(
        title='Persistent',
        name='Persistent',
        prop='persistent',
        color=color_bool,
    ),
    'autostart': DisplayProperty(
        title='Autostart',
        name='Autostart',
        prop='autostart',
        color=color_bool,
    ),
    'managed-save': DisplayProperty(
        title='Managed Save',
        name='Has Managed Save',
        prop='has_managed_save',
        color=color_bool,
    ),
    'current-snapshot': DisplayProperty(
        title='Current Snapshot',
        name='Has Current Snapshot',
        prop='has_current_snapshot',
        color=color_bool,
    ),
    'osType': DisplayProperty(
        title='OS Type',
        name='Guest OS Type',
        prop='os_type',
        color=color_optional,
    ),
    'osArch': DisplayProperty(
        title='Architecture',
        name='Guest CPU Architecture',
        prop='os_arch',
        color=color_optional,
    ),
    'osMachine': DisplayProperty(
        title='Machine',
        name='Guest Machine Type',
        prop='os_machine',
        color=color_optional,
    ),
    'emulator': DisplayProperty(
        title='Emulator',
        name='Emulator Binary',
        prop='emulator',
        color=color_optional,
    ),
    'vcpus': DisplayProperty(
        title='vCPUs',
        name='Current Virtual CPUs',
        prop='current_cpus',
        color=color_optional,
    ),
    'mem': DisplayProperty(
        title='Memory',
        name='Current Memory',
        prop='current_memory',
        use_units=True,
        color=color_optional,
    ),
    'title': DisplayProperty(
        title='Domain Title',
        name='Domain Title',
        prop='title',
        color=color_optional,
    ),
}


class DomainMixin(ObjectMixin):
    '''Mixin for commands that operate on domains.'''
    @property
    def NAME(self: Self) -> str: return 'domain'

    @property
    def CLASS(self: Self) -> Type[Domain]: return Domain

    @property
    def METAVAR(self: Self) -> str: return 'DOMAIN'

    @property
    def LOOKUP_ATTR(self: Self) -> str: return 'domains'

    @property
    def DEFINE_METHOD(self: Self) -> str: return 'define_domain'

    @property
    def CREATE_METHOD(self: Self) -> str: return 'create_domain'

    @property
    def DISPLAY_PROPS(self: Self) -> Mapping[str, DisplayProperty]:
        return _DISPLAY_PROPERTIES

    @property
    def DEFAULT_COLUMNS(self: Self) -> Sequence[str]:
        return (
            'id',
            'name',
            'state',
            'persistent',
            'autostart',
        )

    @property
    def CONFIG_SECTION(self: Self) -> str: return 'domain'
