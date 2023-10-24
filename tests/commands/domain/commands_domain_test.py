# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.domain'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.domain import domain

from ..shared import SRC_ROOT, check_lazy_commands

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


def test_lazy_load(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Test that lazy loading is working at a basic level.

       Also checks the help command.'''
    runner(('domain', 'help'), 0)


def test_check_lazy_command_list() -> None:
    '''Further checks for lazy loading of commands.'''
    check_lazy_commands(domain, SRC_ROOT / 'fvirt' / 'commands' / 'domain')


def test_help_aliases(runner: Callable[[Sequence[str], int], Result]) -> None:
    '''Check that we have an aliases help topic.'''
    # TODO: Should be extended to cross-check against alias list.
    runner(('domain', 'help', 'aliases'), 0)
