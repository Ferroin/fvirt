# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt streams.'''

from __future__ import annotations

import errno
import io
import os
import sys

from typing import TYPE_CHECKING, Self

import libvirt

from typing_extensions import Buffer

from .exceptions import FVirtException, InvalidOperation, PlatformNotSupported

if TYPE_CHECKING:
    from .hypervisor import Hypervisor

DEFAULT_BUFFER_SIZE = 256 * 1024  # 256 kiB


class StreamError(FVirtException):
    '''Raised when a stream encounters an error.'''


class Stream:
    '''Wrapper class for libvirt streams.

       This provides an API mostly compatible with io.RawIOBase from
       the Python standard library, though it lacks a handful of methods
       and includes some extra ones.'''
    __slots__ = (
        '_buf',
        '__error',
        '__finalized',
        '__hv',
        '__interactive',
        '__sparse',
        '__stream',
        '_total',
        '_transferred',
    )

    def __init__(
        self: Self,
        hv: Hypervisor,
        sparse: bool = False,
        interactive: bool = False,
    ) -> None:
        self.__error = False
        self.__finalized = False
        self.__hv = hv
        self.__interactive = interactive
        self.__sparse = sparse
        self._buf = b''
        self._total = 0
        self._transferred = 0

        if interactive and sparse:
            raise ValueError('Interactive mode and sparse mode are mutually exclusive.')

        if sparse and sys.platform == 'win32':
            raise PlatformNotSupported

        hv.open()
        assert hv._connection is not None

        flags = 0

        if interactive:
            flags = libvirt.VIR_STREAM_NONBLOCK

        self.__stream = hv._connection.newStream(flags)

    def __del__(self: Self) -> None:
        self.close()
        self.__hv.close()

    @property
    def stream(self: Self) -> libvirt.virStream:
        '''The underlying stream object.'''
        return self.__stream

    @property
    def closed(self: Self) -> bool:
        '''Whether or not the stream has been closed.'''
        return self.__finalized

    @property
    def transferred(self: Self) -> int:
        '''Total amount of data actually transferred.

           If the stream is in sparse mode, this will not count any
           holes that have been sent.'''
        return self._transferred

    @property
    def total(self: Self) -> int:
        '''Total data processed.

           If the stream is in sparse mode, this will include any bytes
           skipped over because of holes.'''
        return self._total

    @staticmethod
    def _recv_callback(
        _stream: libvirt.virStream,
        data: bytes,
        state: tuple[Stream, io.BufferedRandom],
    ) -> int:
        st, fd = state

        written = 0

        while written < len(data):
            written += fd.write(data[written:])

        st._total += written
        st._transferred += written
        return written

    @staticmethod
    def _recv_hole_callback(
        _stream: libvirt.virStream,
        length: int,
        state: tuple[Stream, io.BufferedRandom],
    ) -> None:
        st, fd = state

        target = fd.seek(length, os.SEEK_CUR)

        try:
            fd.truncate()
        except OSError:
            fd.seek(target, os.SEEK_SET)

        st._total += length

    @staticmethod
    def _send_callback(
        _stream: libvirt.virStream,
        length: int,
        state: tuple[Stream, io.BufferedRandom],
    ) -> bytes:
        st, fd = state
        data = fd.read(length)
        st._total += len(data)
        st._transferred += len(data)
        return data

    @staticmethod
    def _send_hole_callback(
        _steam: libvirt.virStream,
        length: int,
        state: tuple[Stream, io.BufferedRandom],
    ) -> int:
        st, fd = state

        st._total += length
        return fd.seek(length, os.SEEK_CUR)

    @staticmethod
    def _hole_check_callback(
        _stream: libvirt.virStream,
        state: tuple[Stream, io.BufferedRandom],
    ) -> tuple[bool, int]:
        st, fd = state
        current_location = fd.tell()
        in_data = False
        region_length = 0

        try:
            data_start = fd.seek(current_location, os.SEEK_DATA)
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
            hole_start = fd.seek(data_start, os.SEEK_HOLE)

            if hole_start == data_start or hole_start < 0:
                raise RuntimeError

            region_length = hole_start - data_start
        else:
            end_of_file = fd.seek(0, os.SEEK_END)

            if end_of_file < current_location:
                raise RuntimeError

            region_length = end_of_file - current_location

        fd.seek(current_location, os.SEEK_SET)
        return (in_data, region_length)

    def fileno(self: Self) -> None:
        raise OSError

    def isatty(self: Self) -> bool:
        return False

    def seekable(self: Self) -> bool:
        return False

    def readable(self: Self) -> bool:
        return True

    def writable(self: Self) -> bool:
        return True

    def close(self: Self) -> None:
        '''Close the stream.'''
        if not self.__finalized:
            if self.__error:
                self.stream.abort()
            else:
                self.stream.finish()

            self.__finalized = True

    def abort(self: Self) -> None:
        '''Abort any pending stream transfer.'''
        if not self.__finalized:
            self.stream.abort()
            self.__finalized = True

    def read(self: Self, nbytes: int = DEFAULT_BUFFER_SIZE, /) -> bytes:
        '''Read up to nbytes bytes of data from the stream.

           If an error is encountered, StreamError will be raised.

           If the stream is neither sparse nor interactive, a short
           read will only happen at the end of the stream, and this
           call returning an empty bytes object will signal the end of
           the stream.

           If the stream is interactive, short reads will happen whenever
           there is not enough data to return nbytes total. If there is
           no data available, BlockingIOError will be raised.

           If the stream is sparse, a short read may happen before
           any hole in the stream, and a read returning an empty bytes
           object will signal the start of a hole. Holes must be read
           using read_hole(), and a zero-length hole indicates the end
           of the stream.'''
        if nbytes < -1:
            raise ValueError('Number of bytes to read must be at least 1.')

        if nbytes == -1:
            if self.__sparse:
                raise ValueError('Cannot read all data in one call if stream is sparse.')

            ret = b''
            eof = False

            while not eof:
                data = self.read()
                ret += data

                if data == b'':
                    eof = True

            return ret
        else:
            match self.stream.recv(nbytes, libvirt.VIR_STREAM_RECV_STOP_AT_HOLE if self.__sparse else 0):
                case 0:
                    return b''
                case -1:
                    raise StreamError
                case -2:
                    raise BlockingIOError
                case -3:
                    return b''
                case bytes() as b:
                    return b
                case _:
                    raise RuntimeError

    def read_hole(self: Self, /) -> int:
        '''Read the size of a hole in the stream.

           Only valid if the stream is sparse.

           Raises StreamError if there is no hole in the stream.

           Returns 0 if the end of the stream has been reached.

           Otherwise returns the size of the hole.'''
        if not self.__sparse:
            raise InvalidOperation

        match self.stream.recvHole(0):
            case -1:
                raise StreamError
            case int() as i:
                return i
            case _:
                raise RuntimeError

    def read_into_file(self: Self, fd: io.BufferedWriter, /) -> None:
        '''Read all the data from the stream into the file object fd.

           This automatically handles sparse transfers based on whether
           the stream is sparse or not. Also closes the stream when done.'''
        if self.__interactive:
            raise RuntimeError('read_into_file method is not supported for interactive streams.')

        if self.__sparse:
            if not fd.seekable():
                raise ValueError('File specified for read_into_file must be seekable if using a sparse stream.')

            try:
                self.stream.sparseRecvAll(
                    self._recv_callback,
                    self._recv_hole_callback,
                    (self, fd),
                )
            except Exception as e:
                self.__error = True
                raise e
            finally:
                self.close()
        else:
            try:
                self.stream.recvAll(
                    self._recv_callback,
                    (self, fd),
                )
            except Exception as e:
                self.__error = True
                raise e
            finally:
                self.close()

    def write(self: Self, data: Buffer, /) -> int:
        '''Write data to the stream.

           If the stream is interactive and the cannot be written,
           raises BlockingIOError.

           If another error is encountered, raises StreamError.

           Otherwise returns the number of bytes actually written to
           the stream, which may be less than the length of the data
           provided.'''
        match self.stream.send(bytes(data)):
            case -1:
                raise StreamError
            case -2:
                raise BlockingIOError
            case int() as i:
                return i
            case _:
                raise RuntimeError

    def write_hole(self: Self, length: int) -> None:
        '''Write a hole to the stream.

           Only supported if the stream is sparse.

           If an error is encountered, raises StreamError.

           A sparse stream should send a final, zero-length hole before
           closing the stream once it has written all other data.'''
        if length < 0:
            raise ValueError('Hole length may not be negative.')

        match self.stream.sendHole(length):
            case -1:
                raise StreamError
            case 0:
                pass

    def write_from_file(self: Self, fd: io.BufferedRandom) -> None:
        '''Read all of the data from fd and send it over the stream.

           This automatically handles sparse transfers based on whether
           the stream is sparse or not. Also closes the stream when done.'''
        if self.__interactive:
            raise RuntimeError('write_from_file method is not supported for interactive streams.')

        if self.__sparse:
            try:
                self.stream.sparseSendAll(
                    self._send_callback,
                    self._hole_check_callback,
                    self._send_hole_callback,
                    (self, fd),
                )
            except Exception as e:
                self.__error = True
                raise e
            finally:
                self.close()
        else:
            try:
                self.stream.sendAll(
                    self._send_callback,
                    (self, fd),
                )
            except Exception as e:
                self.__error = True
                raise e
            finally:
                self.close()
