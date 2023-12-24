# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine domains.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import DomainMixin
from .._base.lifecycle import UndefineCommand


@final
class _DomainUndefine(UndefineCommand, DomainMixin):
    pass


undefine: Final = _DomainUndefine(
    name='undefine',
)

__all__ = [
    'undefine',
]
