# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Test fixtures for fvirt'''

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from pathlib import Path

import pytest

from simple_file_lock import FileLock


@pytest.fixture(scope='session')
def test_uri() -> str:
    '''Provide the libvirt URI to use for testing.'''
    return 'test:///default'


@pytest.fixture(scope='session')
def live_uri() -> str:
    '''Provide a live libvirt URI to use for testing.'''
    return 'qemu:///session'


@pytest.fixture(scope='session')
def lock_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    '''Provide a session-scoped lock directory.'''
    return tmp_path_factory.mktemp('lock')


@pytest.fixture
def serial(lock_dir: Path) -> Callable[[str], _GeneratorContextManager[None]]:
    '''Provide a callable to serialize parts of a test against other tests.'''
    @contextmanager
    def inner(path: str) -> Generator[None, None, None]:
        with FileLock(lock_dir / path):
            yield

    return inner
