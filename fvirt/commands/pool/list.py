# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import StoragePoolMixin
from .._base.list import ListCommand

EPILOG: Final = '''
For performance reasons, information about the volumes in any given
storage pool is cached by the libvirt daemon. This information is only
updated when a pool is started (or created), when certain operations
(such as defining or deleting volumes) occur, and when the pool is
explicitly refreshed.

This is usually not an issue as the libvirt daemon tracks any changes
made through it, but if some external tool modifies the underlying
storage of the pool, the information shown by this command may not be
accurate any more.

To explicitly refresh the information about the volumes in a storage pool,
use the 'fvirt pool refresh' command.
'''.lstrip().rstrip()


@final
class _PoolList(ListCommand, StoragePoolMixin):
    pass


list_pools: Final = _PoolList(
    name='list',
    epilog=EPILOG,
)

__all__ = [
    'list_pools',
]
