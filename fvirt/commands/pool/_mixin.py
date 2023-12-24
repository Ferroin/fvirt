# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixin for StoragePool related commands.'''

from __future__ import annotations

from typing import Self, Type

from .._base.objects import ObjectMixin
from ...libvirt import StoragePool


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
