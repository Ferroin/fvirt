# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine domains.'''

from __future__ import annotations

from typing import Final, final

from .._base.lifecycle import UndefineCommand
from .._base.objects import DomainMixin
from ...libvirt.domain import MATCH_ALIASES


@final
class _DomainUndefine(UndefineCommand, DomainMixin):
    pass


undefine: Final = _DomainUndefine(
    name='undefine',
    aliases=MATCH_ALIASES,
)

__all__ = [
    'undefine',
]
