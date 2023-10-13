# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.dummy_pool'''

from __future__ import annotations

import concurrent.futures

from fvirt.util.dummy_pool import DummyExecutor


def _check1() -> bool:
    return True


def _check2() -> bool:
    return False


def _check3(a: int) -> int:
    return a


def test_class() -> None:
    '''Verify the ancestry of the DummyExecutor class.'''
    assert issubclass(DummyExecutor, (concurrent.futures.Executor,))


def test_submit() -> None:
    '''Verify that submit works.'''
    e = DummyExecutor()

    futures = (
        e.submit(_check1),
        e.submit(_check2),
        e.submit(_check3, 1),
        e.submit(_check3, a=2),
    )

    results = {f.result() for f in concurrent.futures.as_completed(futures)}

    assert results == {True, False, 1, 2}
