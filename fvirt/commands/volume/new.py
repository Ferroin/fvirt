# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create new volumes.'''

from __future__ import annotations

from typing import Final, final

from .._base.new import NewCommand
from .._base.objects import VolumeMixin


@final
class _NewVolume(NewCommand, VolumeMixin):
    pass


new: Final = _NewVolume()

__all__ = [
    'new',
]
