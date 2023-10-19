# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt streams.'''

from __future__ import annotations

import errno
import io
import os
import sys

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

import libvirt

from .exceptions import PlatformNotSupported

if TYPE_CHECKING:
    from .hypervisor import Hypervisor


@dataclass(kw_only=True, slots=True)
class _StreamState:
    '''State used for stream callbacks.'''
    st: BaseStream
    fd: io.BufferedWriter | io.BufferedRandom


class BaseStream:
    '''Base class for libvirt streams.'''
    def __init__(
        self: Self,
        hv: Hypervisor,
        blocking: bool = True
    ) -> None:
        self._hv = hv
        self._finalized = False
        self._error = False

        hv.open()
        assert hv._connection is not None

        flags = 0

        if not blocking:
            flags |= libvirt.VIR_STREAM_NONBLOCK

        self._stream = hv._connection.newStream(flags)
        self._transferred = 0

    def __del__(self: Self) -> None:
        self.close()
        self._hv.close()

    @property
    def stream(self: Self) -> libvirt.virStream:
        '''The underlying stream object.'''
        return self._stream

    @property
    def closed(self: Self) -> bool:
        '''Whether or not the stream has been closed.'''
        return self._finalized

    def close(self: Self) -> None:
        '''Close the stream.'''
        if not self._finalized:
            if self._error:
                self.stream.abort()
            else:
                self.stream.finish()

            self._finalized = True

    def abort(self: Self) -> None:
        '''Abort any pending stream transfer.'''
        if not self._finalized:
            self.stream.abort()
            self._finalized = True


class BulkStream(BaseStream):
    '''Stream class for bulk synchronous data transfers.'''
    def __init__(
        self: Self,
        hv: Hypervisor,
        sparse: bool = False
    ) -> None:
        self._sparse = sparse

        if sparse and sys.platform == 'win32':
            raise PlatformNotSupported

        self._transferred = 0

        super().__init__(hv, blocking=True)

    @property
    def transferred(self: Self) -> int:
        '''Total amount of data transferred.

           If the stream is in sparse mode, this will not count any
           holes that have been sent.'''
        return self._transferred

    @staticmethod
    def _recv_callback(
        _stream: libvirt.virStream,
        data: bytes,
        state: _StreamState,
    ) -> int:
        written = 0

        assert isinstance(state.st, BulkStream)

        while written < len(data):
            written += state.fd.write(data[written:])

        state.st._transferred += written
        return written

    @staticmethod
    def _recv_hole_callback(
        _stream: libvirt.virStream,
        length: int,
        state: _StreamState,
    ) -> None:
        target = state.fd.seek(length, os.SEEK_CUR)

        try:
            os.ftruncate(state.fd.fileno(), state.fd.tell())
        except OSError:
            state.fd.seek(target, os.SEEK_SET)

    @staticmethod
    def _send_callback(
        _stream: libvirt.virStream,
        length: int,
        state: _StreamState,
    ) -> bytes:
        data = state.fd.read(length)
        state.st._transferred += len(data)
        return data

    @staticmethod
    def _send_hole_callback(
        _steam: libvirt.virStream,
        length: int,
        state: _StreamState,
    ) -> int:
        return state.fd.seek(length, os.SEEK_CUR)

    @staticmethod
    def _hole_check_callback(
        _stream: libvirt.virStream,
        state: _StreamState,
    ) -> tuple[bool, int]:
        current_location = state.fd.tell()
        in_data = False
        region_length = 0

        try:
            data_start = state.fd.seek(current_location, os.SEEK_DATA)
        except OSError as e:
            match e:
                case OSError(errno=errno.ENXIO):
                    data_start = -1
                case _:
                    raise e

        if data_start > current_location:
            region_length = data_start - current_location
        elif data_start == current_location:
            in_data = True
            hole_start = state.fd.seek(data_start, os.SEEK_HOLE)

            if hole_start == data_start or hole_start < 0:
                raise RuntimeError

            region_length = hole_start - data_start
        else:
            end_of_file = state.fd.seek(0, os.SEEK_END)

            if end_of_file < current_location:
                raise RuntimeError

            region_length = end_of_file - current_location

        state.fd.seek(current_location, os.SEEK_SET)
        return (in_data, region_length)

    def recv_into(self: Self, fd: io.BufferedWriter) -> None:
        '''Read all the data from the stream into fd.

           This automatically handles sparse transfers based on whether
           the stream is sparse or not.'''
        state = _StreamState(
            st=self,
            fd=fd,
        )

        if self._sparse:
            try:
                self.stream.sparseRecvAll(
                    self._recv_callback,
                    self._recv_hole_callback,
                    state,
                )
            except Exception as e:
                self._error = True
                raise e
        else:
            try:
                self.stream.recvAll(
                    self._recv_callback,
                    state,
                )
            except Exception as e:
                self._error = True
                raise e

    def send_from(self: Self, fd: io.BufferedRandom) -> None:
        '''Read all of the data from fd and send it over the stream.

           This automatically handles sparse transfers based on whether
           the stream is sparse or not.'''
        state = _StreamState(
            st=self,
            fd=fd,
        )

        if self._sparse:
            try:
                self.stream.sparseSendAll(
                    self._send_callback,
                    self._hole_check_callback,
                    self._send_hole_callback,
                    state,
                )
            except Exception as e:
                self._error = True
                raise e
        else:
            try:
                self.stream.sendAll(
                    self._send_callback,
                    state,
                )
            except Exception as e:
                self._error = True
                raise e
