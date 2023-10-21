# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper for libvirt streams.'''

from __future__ import annotations

import errno
import io
import os
import sys

from dataclasses import dataclass
from enum import Enum, auto, unique
from queue import Empty, Queue
from threading import Event, Thread
from types import TracebackType
from typing import TYPE_CHECKING, BinaryIO, Self

import libvirt

from .exceptions import PlatformNotSupported

if TYPE_CHECKING:
    from pathlib import Path

    from .hypervisor import Hypervisor


@unique
class _StreamOp(Enum):
    '''Indicates the type of stream operation to perform.'''
    DATA = auto()
    HOLE = auto()
    CLOSE = auto()


@dataclass(kw_only=True, slots=True)
class _StreamQueueEntry:
    '''Represents a stream operation in the send or recieve queue.'''
    op: _StreamOp
    len: int | None = None
    buf: bytes | None = None


class _IOWrapper:
    __slots__ = ('__target', '__write', '__obj')

    def __init__(self: Self, target: Path | None, write: bool = False) -> None:
        self.__obj: io.BufferedRandom | None = None
        self.__target = target
        self.__write = write

    def __enter__(self: Self) -> BinaryIO:
        if self.__target is None:
            if self.__write:
                return sys.stdout.buffer
            else:
                return sys.stdin.buffer
        else:
            self.__obj = self.__target.open('w+b' if self.__write else 'r+b')
            return self.__obj

    def __exit__(self: Self, _exc_type: type | None, _exc_value: BaseException | None, _traceback: TracebackType | None) -> None:
        if self.__obj is not None:
            self.__obj.close()


def _send_thread_cb(
    target: Path | None,
    bufsz: int,
    queue: Queue[_StreamQueueEntry],
    done: Event,
    sparse: bool,
    interactive: bool,
) -> None:
    buffer = b''

    with _IOWrapper(target, False) as f:
        while not done.is_set():
            region_length = bufsz
            read_count = bufsz

            if sparse:
                in_data = False
                current_location = f.tell()

                try:
                    data_start = f.seek(current_location, os.SEEK_DATA)
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
                    hole_start = f.seek(data_start, os.SEEK_HOLE)

                    if hole_start == data_start or hole_start < 0:
                        raise RuntimeError

                    region_length = hole_start - data_start
                else:
                    end_of_file = f.seek(0, os.SEEK_END)

                    if end_of_file < current_location:
                        raise RuntimeError

                    region_length = end_of_file - current_location

                if in_data:
                    f.seek(current_location, os.SEEK_SET)

                    if region_length < bufsz:
                        read_count = region_length
                else:
                    queue.put(_StreamQueueEntry(
                        op=_StreamOp.HOLE,
                        len=region_length,
                    ))

                    continue

            buffer = f.read(read_count)

            if interactive and b'\x1b[' in buffer:
                buffer.replace(b'\x1b[', b'')

                queue.put(_StreamQueueEntry(
                    op=_StreamOp.DATA,
                    buf=buffer,
                    len=len(buffer),
                ))
                queue.put(_StreamQueueEntry(
                    op=_StreamOp.CLOSE,
                ))
                break
            elif len(buffer) == 0:
                queue.put(_StreamQueueEntry(
                    op=_StreamOp.CLOSE,
                ))
                break
            else:
                queue.put(_StreamQueueEntry(
                    op=_StreamOp.DATA,
                    buf=buffer,
                    len=region_length,
                ))


def _recv_thread_cb(
    target: Path | None,
    queue: Queue[_StreamQueueEntry],
    done: Event,
    sparse: bool,
) -> None:
    with _IOWrapper(target, False) as f:
        while not done.is_set():
            try:
                match queue.get(block=True, timeout=1):
                    case _StreamQueueEntry(op=_StreamOp.DATA, buf=bytes() as buffer):
                        written = 0

                        while written < len(buffer):
                            written += f.write(buffer[written:])
                    case _StreamQueueEntry(op=_StreamOp.HOLE, len=int() as length):
                        if sparse:
                            try:
                                f.seek(length, os.SEEK_CUR)
                            except OSError:
                                f.write(b'\0' * length)
                            else:
                                try:
                                    os.ftruncate(f.fileno(), f.tell())
                                except OSError:
                                    pass
                        else:
                            f.write(b'\0' * length)
                    case _StreamQueueEntry(op=_StreamOp.CLOSE):
                        break
                    case _:
                        raise RuntimeError
            except Empty:
                pass


class Stream():
    '''Base class for libvirt stream wrappers.'''
    __slots__ = (
        '_buf',
        '__done',
        '__error',
        '__finalized',
        '__hv',
        '__interactive',
        '_pending',
        '__recv_queue',
        '__recv_thread',
        '__send_queue',
        '__send_thread',
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
        qsize: int = 32,
        bufsz: int = 65536,
    ) -> None:
        self.__done = Event()
        self.__error = False
        self.__finalized = False
        self.__hv = hv
        self.__interactive = interactive
        self.__recv_queue: Queue[_StreamQueueEntry] = Queue(qsize)
        self.__recv_thread: Thread | None = None
        self.__send_queue: Queue[_StreamQueueEntry] = Queue(qsize)
        self.__send_thread: Thread | None = None
        self.__sparse = sparse
        self._buf = b''
        self._pending: _StreamQueueEntry | None = None
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

    def __shut_down_threads(self: Self) -> None:
        if not self.__done.is_set():
            self.__done.set()

        if self.__send_thread is not None and self.__send_thread.is_alive():
            self.__send_thread.join()

        if self.__recv_thread is not None and self.__recv_thread.is_alive():
            self.__recv_thread.join()

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
            os.ftruncate(fd.fileno(), fd.tell())
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

    def close(self: Self) -> None:
        '''Close the stream.'''
        self.__shut_down_threads()

        if not self.__finalized:
            if self.__error:
                self.stream.abort()
            else:
                self.stream.finish()

            self.__finalized = True

    def abort(self: Self) -> None:
        '''Abort any pending stream transfer.'''
        self.__shut_down_threads()

        if not self.__finalized:
            self.stream.abort()
            self.__finalized = True

    def recv_into(self: Self, fd: io.BufferedWriter) -> None:
        '''Read all the data from the stream into fd.

           This automatically handles sparse transfers based on whether
           the stream is sparse or not. Also closes the stream when done.'''
        if self.__interactive:
            raise RuntimeError('recv_into method is not supported for interactive streams.')

        if self.__sparse:
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

    def send_from(self: Self, fd: io.BufferedRandom) -> None:
        '''Read all of the data from fd and send it over the stream.

           This automatically handles sparse transfers based on whether
           the stream is sparse or not. Also closes the stream when done.'''
        if self.__interactive:
            raise RuntimeError('send_from method is not supported for interactive streams.')

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
