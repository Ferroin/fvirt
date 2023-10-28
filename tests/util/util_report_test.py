# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.units'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING

import pytest

from fvirt.util.report import summary

if TYPE_CHECKING:
    from collections.abc import Mapping

HEADER_REGEX = re.compile(r'^Results:$', re.MULTILINE)
SUCCESS_REGEX = re.compile(r'^  Success: +([0-9]+)$', re.MULTILINE)
FAILED_REGEX = re.compile(r'^  Failed: +([0-9]+)$', re.MULTILINE)
TOTAL_REGEX = re.compile(r'^Total: +([0-9]+)$', re.MULTILINE)
SKIPPED_REGEX = re.compile(r'^    Skipped: +([0-9]+)$', re.MULTILINE)
FORCED_REGEX = re.compile(r'^    Forced: +([0-9]+)$', re.MULTILINE)
TIMED_OUT_REGEX = re.compile(r'^    Timed Out: +([0-9]+)$', re.MULTILINE)


@pytest.mark.parametrize('kwa', (
    {
        'total': 10,
        'success': 5,
    },
    {
        'total': 9,
        'success': 4,
        'skipped': 1,
    },
    {
        'total': 10,
        'success': 7,
        'forced': 2,
    },
    {
        'total': 12,
        'success': 0,
        'timed_out': 8,
    },
    {
        'total': 37,
        'success': 12,
        'skipped': 4,
        'forced': 5,
        'timed_out': 13,
    },
))
def test_simple_summary(kwa: Mapping[str, int | bool]) -> None:
    '''Test summary output.'''
    total = kwa['total']
    success = kwa['success']
    skipped = kwa.get('skipped', None)
    forced = kwa.get('forced', None)
    timed_out = kwa.get('timed_out', None)

    result = summary(**kwa)  # type: ignore
    result_lines = result.splitlines()

    assert HEADER_REGEX.match(result_lines[0]) is not None, result

    success_match = SUCCESS_REGEX.search(result)

    assert success_match is not None, result
    assert int(success_match[1]) == success

    failed_match = FAILED_REGEX.search(result)

    assert failed_match is not None, result
    assert int(failed_match[1]) == total - success

    total_match = TOTAL_REGEX.match(result_lines[-1])

    assert total_match is not None, result
    assert int(total_match[1]) == total

    if skipped is not None:
        skipped_match = SKIPPED_REGEX.search(result)

        assert skipped_match is not None
        assert int(skipped_match[1]) == skipped
    else:
        assert SKIPPED_REGEX.search(result) is None

    if forced is not None:
        forced_match = FORCED_REGEX.search(result)

        assert forced_match is not None
        assert int(forced_match[1]) == forced
    else:
        assert FORCED_REGEX.search(result) is None

    if timed_out is not None:
        timed_out_match = TIMED_OUT_REGEX.search(result)

        assert timed_out_match is not None
        assert int(timed_out_match[1]) == timed_out
    else:
        assert TIMED_OUT_REGEX.search(result) is None
