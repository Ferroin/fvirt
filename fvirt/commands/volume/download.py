# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for downloading the contents of a volume.'''

from __future__ import annotations

from typing import Final

from ._mixin import VolumeMixin
from .._base.filetransfer import FileTransferCommand

HELP: Final = '''
Download the contents of a volume to a local file.

POOL specifies what storage pool the source volume is in.

VOLUME specifies which volume to download.

FILE specifies what local file to use. Existing data will be overwritten.

The data that is downloaded will be in whatever format the underlying
volume is in. If it’s a raw volume, the data will be identical to what
the guest OS sees. Otherwise, additional processing may be required to
access things like guest filesystems.

This command does not support fvirt's fail-fast mode, as it only operates
on a single volume.

This command does not support fvirt's idempotent mode, as there is no
logical idmpotent behavior for it.
'''.lstrip().rstrip()


class _VolumeDownload(FileTransferCommand, VolumeMixin):
    pass


download = _VolumeDownload(
    name='download',
    help=HELP,
    transfer_method='download',
    file_mode='w+b',
    support_sparse=True,
    require_file=False,
)
