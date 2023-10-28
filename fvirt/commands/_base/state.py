# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Internal state handling for fvirt commands.'''

from __future__ import annotations

import threading

from concurrent.futures import ThreadPoolExecutor
from typing import Self

from ...libvirt import URI, Hypervisor
from ...libvirt.events import start_libvirt_event_thread
from ...util.dummy_pool import DummyExecutor
from ...util.units import bytes_to_unit, count_integer_digits


class State:
    '''Class representing the internal shared state of the fvirt CLI.'''
    __slots__ = [
        '__fail_fast',
        '__fail_if_no_match',
        '__hypervisor',
        '__idempotent',
        '__jobs',
        '__pool',
        '__thread',
        '__units',
        '__uri',
    ]

    def __init__(self: Self, uri: URI, fail_fast: bool, idempotent: bool, fail_if_no_match: bool, units: str, jobs: int):
        if jobs < 1:
            raise ValueError('Number of jobs must be at least 1')

        self.__fail_fast = fail_fast
        self.__fail_if_no_match = fail_if_no_match
        self.__hypervisor: Hypervisor | None = None
        self.__idempotent = idempotent
        self.__jobs = jobs
        self.__pool: ThreadPoolExecutor | DummyExecutor | None = None
        self.__thread: threading.Thread | None = None
        self.__units = units
        self.__uri = uri

    def __del__(self: Self) -> None:
        if self.__pool is not None:
            self.__pool.shutdown(wait=True, cancel_futures=True)

    @property
    def uri(self: Self) -> URI:
        '''The URI specified to the CLI.'''
        return self.__uri

    @property
    def fail_fast(self: Self) -> bool:
        '''Whether or not fail-fast mode is enabled.'''
        return self.__fail_fast

    @property
    def idempotent(self: Self) -> bool:
        '''Whether or not idempotent mode is enabled.'''
        return self.__idempotent

    @property
    def fail_if_no_match(self: Self) -> bool:
        '''Whether or not fail-if-no-match mode is enabled.'''
        return self.__fail_if_no_match

    @property
    def hypervisor(self: Self) -> Hypervisor:
        '''A Hypervisor instance for this command run.'''
        if self.__hypervisor is None:
            if self.__thread is None:
                self.__thread = start_libvirt_event_thread()

            self.__hypervisor = Hypervisor(hvuri=self.uri)

        return self.__hypervisor

    @property
    def jobs(self: Self) -> int:
        '''The number of jobs to use for concurrent operations.'''
        return self.__jobs

    @property
    def pool(self: Self) -> ThreadPoolExecutor | DummyExecutor:
        '''The thread pool to use for concurrent operations.'''
        if self.__pool is None:
            if self.jobs == 1:
                self.__pool = DummyExecutor()
            else:
                self.__pool = ThreadPoolExecutor(
                    max_workers=self.jobs,
                    thread_name_prefix='fvirt-worker',
                )

        return self.__pool

    def convert_units(self: Self, value: int) -> str:
        '''Convert units for output.'''
        if self.__units in {'raw', 'bytes'}:
            return f'{value:z.0F}'

        v, u = bytes_to_unit(value, iec=(self.__units == 'iec'))

        digits = count_integer_digits(v)

        p = max(4 - digits, 0)

        return f'{v:z#.{p}F} {u}'
