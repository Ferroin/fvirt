# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.list'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.commands.domain.list import COLUMNS, DEFAULT_COLS

from ..shared import check_columns, check_default_columns

if TYPE_CHECKING:
    from fvirt.libvirt.domain import Domain


def test_column_definitions(test_dom: Domain) -> None:
    '''Test that column definitions are valid.'''
    check_columns(COLUMNS, test_dom)


def test_default_columns() -> None:
    '''Test that the default column list is valid.'''
    check_default_columns(COLUMNS, DEFAULT_COLS)


@pytest.mark.xfail(reason='Not yet implemented.')
def test_command_run() -> None:
    '''Test that the command runs correctly.'''
    assert False
