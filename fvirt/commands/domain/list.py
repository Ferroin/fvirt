# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list domains.'''

from __future__ import annotations

from typing import Final, final

from .._base.list import ListCommand
from .._base.objects import DomainMixin
from .._base.tables import Column, color_bool, color_optional
from .._base.terminal import get_terminal
from ...libvirt import DomainState


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


COLUMNS: Final = {
    'id': Column(title='ID', prop='id', right_align=True, color=format_id),
    'name': Column(title='Name', prop='name'),
    'uuid': Column(title='UUID', prop='uuid'),
    'genid': Column(title='GenID', prop='genid', color=color_optional),
    'state': Column(title='State', prop='state', color=color_state),
    'persistent': Column(title='Persistent', prop='persistent', color=color_bool),
    'managed-save': Column(title='Managed Save', prop='has_managed_save', color=color_bool),
    'current-snapshot': Column(title='Current Snapshot', prop='has_current_snapshot', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
    'osType': Column(title='OS Type', prop='os_type', color=color_optional),
    'osArch': Column(title='Architecture', prop='os_arch', color=color_optional),
    'osMachine': Column(title='Machine', prop='os_machine', color=color_optional),
    'emulator': Column(title='Emulator', prop='emulator', color=color_optional),
    'title': Column(title='Domain Title', prop='title'),
}

DEFAULT_COLS: Final = (
    'id',
    'name',
    'state',
    'persistent',
    'autostart',
)

SINGLE_LIST_PROPS: Final = (
    'name',
    'uuid',
    'id',
)


@final
class _DomainList(ListCommand, DomainMixin):
    pass


list_domains: Final = _DomainList(
    name='list',
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
    single_list_props=SINGLE_LIST_PROPS,
)

__all__ = [
    'list_domains',
]
