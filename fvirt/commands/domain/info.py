# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a domain.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import DomainMixin
from .._base.info import InfoCommand


@final
class _DomainInfo(InfoCommand, DomainMixin):
    pass


info: Final = _DomainInfo(
    name='info',
)

__all__ = [
    'info',
]
