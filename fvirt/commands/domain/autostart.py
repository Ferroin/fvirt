# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to set the autostart state for one or more domains.'''

from __future__ import annotations

from typing import Final, final

from .._base.autostart import AutostartCommand
from .._base.objects import DomainMixin
from ...libvirt.domain import MATCH_ALIASES


@final
class _DomainAutostart(AutostartCommand, DomainMixin):
    pass


autostart: Final = _DomainAutostart(
    name='autostart',
    aliases=MATCH_ALIASES,
)

__all__ = (
    'autostart',
)
