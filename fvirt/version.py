# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Version handling and version number for fvirt.'''

from __future__ import annotations

from typing import Any, Self


class VersionNumber:
    '''Minimal wrapper class for version information.'''
    def __init__(self: Self, major: int, minor: int, release: int) -> None:
        if major < 0:
            raise ValueError('Major version number must be non-negative.')

        if minor < 0:
            raise ValueError('Minor version number must be non-negative.')

        if release < 0:
            raise ValueError('Release number must be non-negative.')

        self.__major = major
        self.__minor = minor
        self.__release = release

    def __repr__(self: Self) -> str:
        return f'{ self.major }.{ self.minor }.{ self.release }'

    def __str__(self: Self) -> str:
        return repr(self)

    def __hash__(self: Self) -> int:
        return hash(f'{self.major:0>4}{self.minor:0>4}{self.release:0>4}')

    def __eq__(self: Self, item: Any) -> bool:
        if not isinstance(item, VersionNumber):
            return False

        return (self.major == item.major and
                self.minor == item.minor and
                self.release == item.release)

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

    @staticmethod
    def from_libvirt_version(version: int) -> VersionNumber:
        '''Parse a libvirt version number into a VersionNumber.'''
        vstr = str(version)
        release = int(vstr[-3:].lstrip('0') or '0')
        minor = int(vstr[-6:-3].lstrip('0') or '0')
        major = int(vstr[:-6].lstrip('0') or '0')
        return VersionNumber(major, minor, release)


VERSION = VersionNumber(0, 0, 1)

__all__ = [
    'VERSION',
    'VersionNumber',
]
