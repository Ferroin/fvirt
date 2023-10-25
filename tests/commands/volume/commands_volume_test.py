# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.volume'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.volume import volume

from ..shared import SRC_ROOT, check_lazy_commands

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


def test_lazy_load(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that lazy loading is working at a basic level.

       Also checks the help command.'''
    runner(('volume', 'help'), 0)


def test_check_lazy_command_list() -> None:
    '''Further checks for lazy loading of commands.'''
    check_lazy_commands(volume, SRC_ROOT / 'fvirt' / 'commands' / 'volume')


def test_help_aliases(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Check that we have an aliases help topic.'''
    # TODO: Should be extended to cross-check against alias list.
    result = runner(('volume', 'help', 'aliases'), 0)
    assert len(result.output) != 0


def test_help_topics(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that help for the help command works.'''
    result = runner(('volume', 'help', 'help'), 0)
    assert len(result.output) != 0
