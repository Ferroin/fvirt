# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list domains.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import DomainMixin
from .._base.list import ListCommand


@final
class _DomainList(ListCommand, DomainMixin):
    pass


list_domains: Final = _DomainList(
    name='list',
)

__all__ = [
    'list_domains',
]
