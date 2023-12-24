# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixin for Domain related commands.'''

from __future__ import annotations

from typing import Self, Type

from .._base.objects import ObjectMixin
from ...libvirt import Domain


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
