# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new domain.'''

from __future__ import annotations

from typing import Final, final

from .._base.new import DefineCommand
from .._base.objects import DomainMixin


@final
class _DomainDefine(DefineCommand, DomainMixin):
    pass


define: Final = _DomainDefine(
    name='define',
)

__all__ = [
    'define',
]
