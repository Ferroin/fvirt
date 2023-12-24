# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start domains.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import DomainMixin
from .._base.lifecycle import StartCommand


@final
class _DomainStart(StartCommand, DomainMixin):
    pass


start: Final = _DomainStart(
    name='start',
)

__all__ = [
    'start',
]
