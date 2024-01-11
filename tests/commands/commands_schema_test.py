# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.schema'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.commands._base.config import FVirtConfig
from fvirt.commands._base.exitcode import ExitCode
from fvirt.libvirt.models.domain import DomainInfo
from fvirt.libvirt.models.storage_pool import PoolInfo
from fvirt.libvirt.models.volume import VolumeInfo

from .shared import SCHEMA_FORMATS, check_schema

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result
    from pydantic import BaseModel

SCHEMAS = (
    ('config', FVirtConfig),
    ('domain', DomainInfo),
    ('pool', PoolInfo),
    ('volume', VolumeInfo),
)

SCHEMA_CASES = [
    (x[0], y[0], y[1], x[1]) for x in SCHEMAS for y in SCHEMA_FORMATS
]


@pytest.mark.parametrize('n, f, d, m', SCHEMA_CASES)
def test_schema_command(n: str, f: str, d: Callable[[str], dict], m: type[BaseModel], runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Check output from the schema command.'''
    check_schema('config', f, d, FVirtConfig, runner)


def test_schema_list(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Check the list sub-command for the schema command.'''
    result = runner(('schema', 'list'), 0)

    lines = result.output.splitlines()

    assert len(lines) == (len(SCHEMAS) + 1)

    schemas = {
        x.lstrip().split(':')[0] for x in lines[1:]
    }

    assert schemas == {x[0] for x in SCHEMAS}


def test_invalid_schema(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Confirm that passing an invalid schema returns an error.'''
    runner(('schema', 'bogus'), ExitCode.BAD_ARGUMENTS)
