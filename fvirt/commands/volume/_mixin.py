# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixin for Volume related commands.'''

from __future__ import annotations

from typing import TYPE_CHECKING, Self, Type

from .._base.objects import DisplayProperty, ObjectMixin
from .._base.tables import color_optional
from ...libvirt import Volume

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class VolumeMixin(ObjectMixin):
    @property
    def NAME(self: Self) -> str: return 'volume'

    @property
    def CLASS(self: Self) -> Type[Volume]: return Volume

    @property
    def METAVAR(self: Self) -> str: return 'VOLUME'

    @property
    def LOOKUP_ATTR(self: Self) -> str: return 'volumes'

    @property
    def DEFINE_METHOD(self: Self) -> str: return 'define_volume'

    @property
    def PARENT_NAME(self: Self) -> str: return 'storage pool'

    @property
    def PARENT_METAVAR(self: Self) -> str: return 'POOL'

    @property
    def PARENT_ATTR(self: Self) -> str: return 'storage_pools'

    @property
    def DISPLAY_PROPS(self: Self) -> Mapping[str, DisplayProperty]:
        return {
            'name': DisplayProperty(
                title='Name',
                name='Name',
                prop='name',
            ),
            'key': DisplayProperty(
                title='Key',
                name='Key',
                prop='key',
            ),
            'type': DisplayProperty(
                title='Type',
                name='Volume Type',
                prop='vol_type',
            ),
            'format': DisplayProperty(
                title='Format',
                name='Volume Format',
                prop='format',
            ),
            'path': DisplayProperty(
                title='Path',
                name='Volume Path',
                prop='path',
                color=color_optional,
            ),
            'capacity': DisplayProperty(
                title='Capacity',
                name='Total Capacity',
                prop='capacity',
                right_align=True,
                use_units=True,
            ),
            'allocated': DisplayProperty(
                title='Allocated',
                name='Allocated Space',
                prop='allocated',
                right_align=True,
                use_units=True,
            ),
        }

    @property
    def DEFAULT_COLUMNS(self: Self) -> Sequence[str]:
        return (
            'name',
            'path',
            'capacity',
        )
