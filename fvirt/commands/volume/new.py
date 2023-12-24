# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to create new volumes.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import VolumeMixin
from .._base.new import NewCommand


@final
class _NewVolume(NewCommand, VolumeMixin):
    pass


new: Final = _NewVolume()

__all__ = [
    'new',
]
