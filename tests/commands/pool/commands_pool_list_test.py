# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.list'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.pool.list import COLUMNS, DEFAULT_COLS

from ..shared import check_columns, check_default_columns

if TYPE_CHECKING:
    from fvirt.libvirt.storage_pool import StoragePool


def test_column_definitions(test_pool: StoragePool) -> None:
    '''Test that column definitions are valid.'''
    check_columns(COLUMNS, test_pool)


def test_default_columns() -> None:
    '''Test that the default column list is valid.'''
    check_default_columns(COLUMNS, DEFAULT_COLS)
