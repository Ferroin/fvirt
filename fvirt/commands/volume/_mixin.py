# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixin for Volume related commands.'''

from __future__ import annotations

from typing import Self, Type

from .._base.objects import ObjectMixin
from ...libvirt import Volume


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
