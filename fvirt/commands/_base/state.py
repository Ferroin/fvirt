# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Internal state handling for fvirt commands.'''

from __future__ import annotations

import threading

from typing import Self

from ...libvirt import URI, Hypervisor
from ...libvirt.events import start_libvirt_event_thread


class State:
    '''Class representing the internal shared state of the fvirt CLI.'''
    __slots__ = [
        '__uri',
        '__thread',
        '__hypervisor',
        '__fail_fast',
        '__idempotent',
        '__fail_if_no_match',
    ]

    def __init__(self: Self, uri: URI, fail_fast: bool, idempotent: bool, fail_if_no_match: bool):
        self.__thread: threading.Thread | None = None
        self.__hypervisor: Hypervisor | None = None
        self.__uri = uri
        self.__fail_fast = fail_fast
        self.__idempotent = idempotent
        self.__fail_if_no_match = fail_if_no_match

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
