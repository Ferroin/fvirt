# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to set the autostart state for one or more domains.'''

from __future__ import annotations

from typing import Final

from .._base.autostart import AutostartCommand
from ...libvirt.domain import MATCH_ALIASES

autostart: Final = AutostartCommand(
    name='autostart',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    doc_name='domain',
)

__all__ = (
    'autostart',
)
