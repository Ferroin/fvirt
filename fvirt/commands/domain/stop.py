# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to stop domains.'''

from __future__ import annotations

from typing import Final, final

from .._base.lifecycle import StopCommand
from .._base.objects import DomainMixin


@final
class _DomainStop(StopCommand, DomainMixin):
    pass


stop: Final = _DomainStop(
    name='stop',
)

__all__ = [
    'stop',
]
