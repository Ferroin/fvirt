# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Dummy concurrent.futures.Executor implementation for unparallelizing things.

   This is used in the fvirt.commands code when a user requests that
   everything runs as a single job so that we can avoid the overhead of
   creating a thread pool with only one thread.'''

from __future__ import annotations

from concurrent.futures import Executor, Future
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable


class DummyExecutor(Executor):
    '''An Executor subclass that just runs all calls synchronously.

       This can be used to serialize calls in code that uses
       concurrent.futures, which is useful for avoiding the overhead of
       spawning new threads or processes when you only want one thing
       running at a time.'''
    def submit(self: Self, fn: Callable, /, *args: Any, **kwargs: Any) -> Future:
        ret: Future = Future()

        ret.set_running_or_notify_cancel()

        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            ret.set_exception(e)
        else:
            ret.set_result(result)

        return ret
