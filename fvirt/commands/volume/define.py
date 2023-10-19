# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new volume.'''

from __future__ import annotations

from typing import Final, final

from .._base.new import DefineCommand
from .._base.objects import VolumeMixin


@final
class _VolDefine(DefineCommand, VolumeMixin):
    pass


define: Final = _VolDefine(
    name='define',
)

__all__ = [
    'define',
]
