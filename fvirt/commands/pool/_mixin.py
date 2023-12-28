# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixin for StoragePool related commands.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Self, Type

from .._base.objects import DisplayProperty, ObjectMixin
from .._base.tables import color_bool, color_optional
from .._base.terminal import get_terminal
from ...libvirt.storage_pool import StoragePool, StoragePoolState

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def color_state(value: StoragePoolState) -> str:
    '''Apply colors to a pool state.'''
    TERM = get_terminal()

    match value:
        case s if s in {StoragePoolState.RUNNING}:
            return TERM.bright_green_on_black(str(value))
        case s if s in {StoragePoolState.BUILDING}:
            return TERM.bright_yellow_on_black(str(value))
        case s if s in {StoragePoolState.DEGRADED, StoragePoolState.INACCESSIBLE}:
            return TERM.bright_red_on_black(str(value))
        case _:
            return str(value)

    raise RuntimeError  # Needed because mypy thinks the above case statement is non-exhaustive.


class StoragePoolMixin(ObjectMixin):
    '''Mixin for commands that operate on storage pools.'''
    @property
    def NAME(self: Self) -> str: return 'storage pool'

    @property
    def CLASS(self: Self) -> Type[StoragePool]: return StoragePool

    @property
    def METAVAR(self: Self) -> str: return 'POOL'

    @property
    def LOOKUP_ATTR(self: Self) -> str: return 'storage_pools'

    @property
    def DEFINE_METHOD(self: Self) -> str: return 'define_storage_pool'

    @property
    def CREATE_METHOD(self: Self) -> str: return 'create_storage_pool'

    @property
    def DISPLAY_PROPS(self: Self) -> Mapping[str, DisplayProperty]:
        return {
            'name': DisplayProperty(
                title='Name',
                name='Name',
                prop='name',
            ),
            'uuid': DisplayProperty(
                title='UUID',
                name='UUID',
                prop='uuid',
            ),
            'state': DisplayProperty(
                title='State',
                name='state',
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
            'type': DisplayProperty(
                title='Type',
                name='Pool Type',
                prop='pool_type',
                color=color_optional,
            ),
            'format': DisplayProperty(
                title='Format',
                name='Pool Format',
                prop='format',
                color=color_optional,
            ),
            'dir': DisplayProperty(
                title='Directory',
                name='Pool Directory',
                prop='dir',
                color=color_optional,
            ),
            'device': DisplayProperty(
                title='Device',
                name='Pool Device',
                prop='device',
                color=color_optional,
            ),
            'target': DisplayProperty(
                title='Target',
                name='Pool Target',
                prop='target',
                color=color_optional,
            ),
            'volumes': DisplayProperty(
                title='Volumes',
                name='Volumes',
                prop='num_volumes',
                right_align=True,
                color=color_optional,
            ),
            'capacity': DisplayProperty(
                title='Capacity',
                name='Total Capacity',
                prop='capacity',
                right_align=True,
                color=color_optional,
                use_units=True,
            ),
            'allocated': DisplayProperty(
                title='Allocated',
                name='Allocated Space',
                prop='allocated',
                right_align=True,
                color=color_optional,
                use_units=True,
            ),
            'available': DisplayProperty(
                title='Available',
                name='Available Space',
                prop='available',
                right_align=True,
                color=color_optional,
                use_units=True,
            ),
        }

    @property
    def DEFAULT_COLUMNS(self: Self) -> Sequence[str]:
        return (
            'name',
            'type',
            'format',
            'state',
            'autostart',
            'volumes',
            'capacity',
            'available',
        )
