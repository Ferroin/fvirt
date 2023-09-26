# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Terminal handling for the fvirt CLI.'''

from __future__ import annotations

import blessed

TERM = blessed.Terminal()

__all__ = [
    'TERM',
]
