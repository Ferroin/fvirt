# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models._types.'''

from __future__ import annotations

from typing import Type

import pytest

from fvirt.libvirt.models._types import CustomBool, OnOff, YesNo


@pytest.mark.parametrize('t, true_str, false_str', (
    (OnOff, 'on', 'off'),
    (YesNo, 'yes', 'no'),
))
def test_custom_bools(t: Type[CustomBool], true_str: str, false_str: str) -> None:
    '''Test custom boolean types.'''
    assert bool(t(true_str))
    assert not bool(t(false_str))
    assert bool(t(True))
    assert not bool(t(False))

    assert str(t(true_str)) == true_str
    assert str(t(false_str)) == false_str
    assert str(t(True)) == true_str
    assert str(t(False)) == false_str

    assert hash(t(true_str)) == hash(True)
    assert hash(t(false_str)) == hash(False)
    assert hash(t(True)) == hash(True)
    assert hash(t(False)) == hash(False)
