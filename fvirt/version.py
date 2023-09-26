# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Version handling and version number for fvirt.'''

from __future__ import annotations

from typing import Self


class VersionNumber:
    '''Minimal wrapper class for version information.'''
    def __init__(self: Self, major: int, minor: int, release: int) -> None:
        self.__major = major
        self.__minor = minor
        self.__release = release

    def __repr__(self: Self) -> str:
        return f'{ self.major }.{ self.minor }.{ self.release }'

    def __str__(self: Self) -> str:
        return repr(self)

    def __getitem__(self: Self, idx: int) -> int:
        match idx:
            case 0:
                return self.major
            case 1:
                return self.minor
            case 2:
                return self.release
            case _:
                raise IndexError

    @property
    def major(self: Self) -> int:
        '''The major version number.'''
        return self.__major

    @property
    def minor(self: Self) -> int:
        '''The minor version number.'''
        return self.__minor

    @property
    def release(self: Self) -> int:
        '''The release release number.'''
        return self.__release


VERSION = VersionNumber(0, 0, 1)

__all__ = [
    'VERSION',
    'VersionNumber',
]
