# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.cli'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


def test_bare_invoke(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that we actually run at all.'''
    runner(tuple(), 2)


def test_load_check(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that lazy loading doesn’t run into any major issues.'''
    result = runner(('help',), 0)
    assert len(result.output) != 0


def test_help_topics(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that help for the help command works.'''
    result = runner(('help', 'help'), 0)
    assert len(result.output) != 0
