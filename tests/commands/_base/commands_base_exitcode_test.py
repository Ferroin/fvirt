# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands._base.exitcode'''

from __future__ import annotations

from fvirt.commands._base.exitcode import ExitCode


def test_success_is_0() -> None:
    '''Confirm that ExitCode.SUCCESS has a value of 0.'''
    assert ExitCode.SUCCESS.value == 0
