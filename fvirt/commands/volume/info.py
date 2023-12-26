# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a volume.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import VolumeMixin
from .._base.info import InfoCommand


@final
class _VolInfo(InfoCommand, VolumeMixin):
    pass


info: Final = _VolInfo(
    name='info',
)

__all__ = [
    'info',
]
