# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host.uri'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


def test_uri(runner: Callable[[Sequence[str], int], Result], test_uri: str) -> None:
    '''Test that the host uri command properly reports the URI.'''
    result = runner(('-c', test_uri, 'host', 'uri'), 0)
    assert result.output == f'{ test_uri }\n'
