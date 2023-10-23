# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.info'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.commands.pool.info import INFO_ITEMS

from ..shared import check_info_items

if TYPE_CHECKING:
    from fvirt.libvirt.storage_pool import StoragePool


def test_info_items(test_pool: StoragePool) -> None:
    '''Test that the defined info items are valid.'''
    check_info_items(INFO_ITEMS, test_pool)


@pytest.mark.xfail(reason='Not yet implemented.')
def test_command_run() -> None:
    '''Test that the command runs correctly.'''
    assert False
