# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for uploading the contents of a volume.'''

from __future__ import annotations

from typing import Final

import click

from ._mixin import VolumeMixin
from .._base.filetransfer import FileTransferCommand

HELP: Final = '''
Upload the contents of a local file to a volume.

POOL specifies what storage pool the target volume is in.

VOLUME specifies which volume to upload to.

FILE specifies what local file to use.

The data that is uploaded should be in whatever format the underlying
volume is in. If uploading an ISO image, a raw disk image, or the contents
of a local block device, the volume should have a format of 'raw'.

This command does not support fvirt's fail-fast mode, as it only operates
on a single volume.

This command does not support fvirt's idempotent mode, as there is no
logical idmpotent behavior for it.
'''.lstrip().rstrip()


class _VolumeUpload(FileTransferCommand, VolumeMixin):
    pass


upload = _VolumeUpload(
    name='upload',
    help=HELP,
    transfer_method='upload',
    file_mode='r+b',
    support_sparse=True,
    require_file=True,
    params=(click.Option(
        param_decls=('--resize',),
        is_flag=True,
        default=False,
        help='Resize the volume to match the size of the file being uploaded.',
    ),)
)
