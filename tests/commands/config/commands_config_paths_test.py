# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.config.paths'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


def test_config_paths_command(runner: Callable[[Sequence[str], int, bool], Result], test_configs: None) -> None:
    '''Check that the config paths command works correctly.'''
    from fvirt.commands._base.config import CONFIG_PATHS

    result = runner(('config', 'paths'), 0, False)

    items = result.stdout.splitlines()

    assert len(items) == len(CONFIG_PATHS), result.stdout

    for idx, item in enumerate(items):
        if idx == 0:
            path, _, marker = item.rpartition(' ')

            assert path == str(CONFIG_PATHS[0])
            assert marker == '*'
        else:
            assert item == str(CONFIG_PATHS[idx])
