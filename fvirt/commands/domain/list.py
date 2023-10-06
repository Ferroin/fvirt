# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list domains.'''

from __future__ import annotations

from typing import Any

from .._base.list import ListCommand
from ...libvirt import DomainState
from ...libvirt.domain import MATCH_ALIASES
from ...util.tables import Column, color_bool
from ...util.terminal import get_terminal


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


def format_optional_attrib(value: Any) -> str:
    '''Format an optionally empty attribute.'''
    if value is None:
        return '-'
    else:
        return str(value)


COLUMNS = {
    'id': Column(title='ID', prop='id', right_align=True, color=format_id),
    'name': Column(title='Name', prop='name'),
    'uuid': Column(title='UUID', prop='uuid'),
    'genid': Column(title='GenID', prop='genid'),
    'state': Column(title='State', prop='state', color=color_state),
    'persistent': Column(title='Persistent', prop='persistent', color=color_bool),
    'managed-save': Column(title='Managed Save', prop='hasManagedSave', color=color_bool),
    'current-snapshot': Column(title='Current Snapshot', prop='hasCurrentSnapshot', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
    'osType': Column(title='OS Type', prop='osType', color=format_optional_attrib),
    'osArch': Column(title='Architecture', prop='osArch', color=format_optional_attrib),
    'osMachine': Column(title='Machine', prop='osMachine', color=format_optional_attrib),
    'emulator': Column(title='Emulator', prop='emulator'),
    'title': Column(title='Domain Title', prop='title'),
}

DEFAULT_COLS = (
    'id',
    'name',
    'state',
    'persistent',
    'autostart',
)

list_domains = ListCommand(
    name='list',
    aliases=MATCH_ALIASES,
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
    hvprop='domains',
    doc_name='domain',
    single_list_props=(
        'name',
        'uuid',
        'id',
    ),
)

__all__ = [
    'list_domains',
]
