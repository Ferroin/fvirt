# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Definitions for exit codes for the fvirt command.'''

from __future__ import annotations

from enum import IntEnum, unique


@unique
class ExitCode(IntEnum):
    '''Enumerable of exit codes for fvirt.'''
    SUCCESS = 0
    BAD_ARGUMENTS = 1
    GENERAL_FAILURE = 2
    ENTITY_NOT_FOUND = 3
    PARENT_NOT_FOUND = 4
    OPERATION_FAILED = 5
    PATH_NOT_VALID = 6
