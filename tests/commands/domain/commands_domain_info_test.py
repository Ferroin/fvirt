# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.info'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.commands.domain.info import INFO_ITEMS

from ..shared import check_info_items

if TYPE_CHECKING:
    from fvirt.libvirt.domain import Domain


def test_info_items(test_dom: Domain) -> None:
    '''Test that the defined info items are valid.'''
    check_info_items(INFO_ITEMS, test_dom)


@pytest.mark.xfail(reason='Not yet implemented.')
def test_command_run() -> None:
    '''Test that the command runs correctly.'''
    assert False
