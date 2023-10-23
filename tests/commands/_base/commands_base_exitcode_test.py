# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands._base.exitcode'''

from __future__ import annotations

import pytest

from fvirt.commands._base.exitcode import ExitCode


def test_success_is_0() -> None:
    '''Confirm that ExitCode.SUCCESS has a value of 0.'''
    assert ExitCode.SUCCESS.value == 0


@pytest.mark.parametrize('v', (
    x for x in ExitCode if x is not ExitCode.SUCCESS
))
def test_non_success_values(v: ExitCode) -> None:
    '''Confirm that ExitCode values other than ExitCode.SUCCESS are valid exit codes.'''
    assert v > 0
    assert v < 127
