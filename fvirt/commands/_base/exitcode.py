# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Definitions for exit codes for the fvirt command.'''

from __future__ import annotations

from enum import IntEnum, unique


@unique
class ExitCode(IntEnum):
    '''Enumerable of exit codes for fvirt.'''
    SUCCESS = 0
    FAILURE = 1
    ENTITY_NOT_FOUND = 2
    PARENT_NOT_FOUND = 3
    OPERATION_FAILED = 4
