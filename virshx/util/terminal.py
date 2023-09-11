# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Terminal handling for virshx CLI.'''

from __future__ import annotations

import blessed

TERM = blessed.Terminal()

__all__ = [
    'TERM',
]
