# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.host import host

from ..shared import SRC_ROOT, check_lazy_commands

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


def test_lazy_load(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that lazy loading is working at a basic level.

       Also checks the help command.'''
    runner(('host', 'help'), 0)


def test_check_lazy_command_list() -> None:
    '''Further checks for lazy loading of commands.'''
    check_lazy_commands(host, SRC_ROOT / 'fvirt' / 'commands' / 'host')


def test_help_topics(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that help for the help command works.'''
    result = runner(('host', 'help', 'help'), 0)
    assert len(result.output) != 0
