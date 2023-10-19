# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start domains.'''

from __future__ import annotations

from typing import Final, final

from .._base.lifecycle import StartCommand
from .._base.objects import DomainMixin
from ...libvirt.domain import MATCH_ALIASES


@final
class _DomainStart(StartCommand, DomainMixin):
    pass


start: Final = _DomainStart(
    name='start',
    aliases=MATCH_ALIASES,
)

__all__ = [
    'start',
]
