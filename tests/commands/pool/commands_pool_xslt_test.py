# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.xslt'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from click.testing import Result

    from fvirt.libvirt import StoragePool


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool: StoragePool,
    xslt_doc_factory: Callable[[str, str], str],
    tmp_path: Path,
) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_pool._hv.uri)
    xslt_path = tmp_path / 'transform.xslt'

    e = live_pool.config.find('/target/path')
    assert e is not None

    xslt_path.write_text(xslt_doc_factory('target/path', str(tmp_path)))

    result = runner(('-c', uri, 'pool', 'xslt', live_pool.name, str(xslt_path)), 0)

    assert len(result.output) > 0

    e = live_pool.config.find('/target/path')
    assert e is not None

    assert e.text == str(tmp_path)


@pytest.mark.xfail(reason='Test not yet implemented')
def test_command_bulk_run() -> None:
    '''Test running the command on multiple objects.'''
    assert False
