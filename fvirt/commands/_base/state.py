# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Internal state handling for fvirt commands.'''

from __future__ import annotations

import logging
import logging.config
import os
import sys

from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Self, TypeVar, cast

from .config import FVirtConfig, LoggingConfig, get_config

if TYPE_CHECKING:
    import threading

    from concurrent.futures import ThreadPoolExecutor

    from ...libvirt import URI, Hypervisor
    from ...util.dummy_pool import DummyExecutor

T = TypeVar('T')

LOGGER: Final = logging.getLogger(__name__)
DEFAULT_MAX_JOBS: Final = 8
NCPUS: Final = os.cpu_count()

if NCPUS is not None:
    DEFAULT_JOB_COUNT = min(DEFAULT_MAX_JOBS, NCPUS + 4)
else:
    DEFAULT_JOB_COUNT = DEFAULT_MAX_JOBS

if hasattr(os, 'sched_getaffinity') and os.sched_getaffinity(0):
    DEFAULT_JOB_COUNT = min(DEFAULT_MAX_JOBS, len(os.sched_getaffinity(0)) + 4)


def _configure_logging(config: LoggingConfig) -> None:
    if sys.stderr.isatty() and not config.full_log_output:
        stderr_formatter = 'stderr'
    else:
        stderr_formatter = 'full'

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'stderr': {
                'format': '%(message)s',
            },
            'full': {
                'format': '%(asctime)s : %(levelname)s : %(name)s : %(message)s',
            },
        },
        'handlers': {
            'stderr': {
                'class': 'logging.StreamHandler',
                'stream': sys.stderr,
                'formatter': stderr_formatter,
                'level': config.level,
            },
        },
        'root': {
            'handlers': [
                'stderr',
            ],
            'level': config.level,
        },
        'disable_existing_loggers': False,
    })


def _effective(config: FVirtConfig, uri: URI, key: str, override: T | None, default: T) -> T:
    if override is not None:
        return override

    if (v := getattr(config.get_effective_config(uri), key, None)) is not None:
        return cast(T, v)

    return default


class State:
    '''Class representing the internal shared state of the fvirt CLI.'''
    __slots__ = [
        '__config',
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

    def __init__(
        self: Self,
        config_file: Path | None,
        uri: URI,
        fail_fast: bool | None,
        idempotent: bool | None,
        fail_if_no_match: bool | None,
        units: str | None,
        jobs: int | None,
        log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] | None,
    ) -> None:
        if jobs == 0:
            jobs = DEFAULT_JOB_COUNT

        if isinstance(jobs, int) and jobs < 1:
            raise ValueError('Number of jobs must be at least 1')

        self.__config = get_config(config_file)

        if log_level is not None:
            self.config.log.level = log_level

        _configure_logging(self.config.log)

        self.__uri = uri
        LOGGER.info(f'Using libvirt URI: {uri}')

        self.__fail_fast = _effective(self.config, self.uri, 'fail_fast', fail_fast, False)
        LOGGER.info(f'Fail-fast: {"enabled" if self.fail_fast else "disabled"}')

        self.__fail_if_no_match = _effective(self.config, self.uri, 'fail_if_no_match', fail_if_no_match, False)
        LOGGER.info(f'Fail-if-no-match: {"enabled" if self.fail_if_no_match else "disabled"}')

        self.__idempotent = _effective(self.config, self.uri, 'idempotent', idempotent, True)
        LOGGER.info(f'Idempotent: {"enabled" if self.idempotent else "disabled"}')

        self.__jobs = _effective(self.config, self.uri, 'jobs', jobs, DEFAULT_JOB_COUNT)
        LOGGER.debug(f'Jobs: {self.jobs}')

        self.__units = _effective(self.config, self.uri, 'units', units, 'si')
        LOGGER.debug(f'Units: {self.__units}')

        self.__hypervisor: Hypervisor | None = None
        self.__pool: ThreadPoolExecutor | DummyExecutor | None = None
        self.__thread: threading.Thread | None = None

    def __del__(self: Self) -> None:
        if self.__pool is not None:
            self.__pool.shutdown(wait=True, cancel_futures=True)

    @property
    def config(self: Self) -> FVirtConfig:
        '''The configuration for this instance of fvirt.'''
        return self.__config

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
                from ...libvirt.events import start_libvirt_event_thread

                self.__thread = start_libvirt_event_thread()

            from ...libvirt.hypervisor import Hypervisor

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
                LOGGER.debug('Creating fake thread pool for serialized execution.')

                from ...util.dummy_pool import DummyExecutor

                self.__pool = DummyExecutor()
            else:
                LOGGER.info(f'Starting thread pool with {self.jobs} threads.')

                from concurrent.futures import ThreadPoolExecutor

                self.__pool = ThreadPoolExecutor(
                    max_workers=self.jobs,
                    thread_name_prefix='fvirt-worker',
                )

        return self.__pool

    def convert_units(self: Self, value: int) -> str:
        '''Convert units for output.'''
        if self.__units in {'raw', 'bytes'}:
            return f'{value:z.0F}'

        from ...util.units import bytes_to_unit, count_integer_digits

        v, u = bytes_to_unit(value, iec=(self.__units == 'iec'))

        digits = count_integer_digits(v)

        p = max(4 - digits, 0)

        return f'{v:z#.{p}F} {u}'
