# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.shutdown'''

from __future__ import annotations

import pytest


@pytest.mark.xfail(reason='Requires live domain testing.')
def test_command_run() -> None:
    '''Test that the command runs correctly.'''
    assert False
