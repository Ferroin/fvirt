# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Libvirt event handling code for fvirt.'''

from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import threading

LOGGER: Final = logging.getLogger(__name__)


def _event_loop_thread() -> None:
    '''Thread body for the thread returned by start_libvirt_event_thread.'''
    import libvirt

    from .exceptions import call_libvirt

    while True:
        call_libvirt(lambda: libvirt.virEventRunDefaultImpl())


def _event_dummy_timer_cb(_id: int, _opaque: None) -> None:
    '''Dummy timer event handler.

       Used to register a timer event on the event loop before starting
       it to prevent hangs.'''
    pass


def start_libvirt_event_thread() -> threading.Thread:
    '''Start a thread running the libvirt default event loop implementation.

       If you aren’t handling events yourself, you need to call this
       function exactly once prior to establishing your first Hypervisor
       connection, otherwise reconnect handling will not work correctly
       (among other things).'''
    import threading

    import libvirt

    from .exceptions import call_libvirt

    LOGGER.info('Starting libvirt event handling thread')
    call_libvirt(lambda: libvirt.virEventRegisterDefaultImpl())
    call_libvirt(lambda: libvirt.virEventAddTimeout(60000, _event_dummy_timer_cb, None))

    t = threading.Thread(
        target=_event_loop_thread,
        name='libvirt-events',
        daemon=True,
    )

    t.start()

    return t
