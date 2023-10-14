# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared code for tests for fvirt.commands'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.libvirt.entity import Entity
from fvirt.util.tables import Column

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def check_columns(cols: Mapping[str, Column], sample: Entity) -> None:
    '''CHeck that a mapping of columns is valid.'''
    for k, v in cols.items():
        assert isinstance(k, str)
        assert isinstance(v, Column)
        assert v.prop in dir(sample)

    assert len({x.title for x in cols.values()}) == len(cols)


def check_default_columns(cols: Mapping[str, Column], default: Sequence[str]) -> None:
    '''Check that a list of default columns is valid.'''
    for k in default:
        assert k in cols
