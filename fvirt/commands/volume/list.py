# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import VolumeMixin
from .._base.list import ListCommand


@final
class _VolList(ListCommand, VolumeMixin):
    pass


list_volumes: Final = _VolList(
    name='list',
)

__all__ = [
    'list_volumes',
]
