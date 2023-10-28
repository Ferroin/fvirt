# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command result summary handling functions.'''

from __future__ import annotations

from .units import count_integer_digits


def summary(
    *,
    total: int,
    success: int,
    idempotent: bool = False,
    skipped: int = 0,
    forced: int = 0,
    timed_out: int = 0,
) -> str:
    '''Produce a summary of the results of a command.'''
    ret = ''
    indent = '  '
    width = 1 + count_integer_digits(total)
    line = '{0: <15s}{1: >{2}d}\n'

    ret += 'Results:\n'
    ret += line.format(
        indent * 1 + 'Success:',
        success,
        width,
    )

    if idempotent and skipped:
        ret += line.format(
            indent * 2 + 'Skipped:',
            skipped,
            width,
        )

    ret += line.format(
        indent * 1 + 'Failed:',
        total - success,
        width,
    )

    if not idempotent and skipped:
        ret += line.format(
            indent * 2 + 'Skipped:',
            skipped,
            width,
        )

    if forced:
        ret += line.format(
            indent * 2 + 'Forced:',
            forced,
            width,
        )

    if timed_out:
        ret += line.format(
            indent * 2 + 'Timed Out:',
            timed_out,
            width,
        )

    ret += line.format(
        indent * 0 + 'Total:',
        total,
        width,
    )

    return ret.rstrip()
