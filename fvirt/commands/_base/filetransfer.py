# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Classes for fvirt commands that copy data to or from a local file.'''

from __future__ import annotations

import logging

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Self

import click

from .command import Command
from .exitcode import ExitCode
from .objects import is_object_mixin

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .state import State

LOGGER: Final = logging.getLogger(__name__)


class FileTransferCommand(Command):
    '''Command class for performing file transfers to/from the hypervisor.

       This handles the required callback and parameters.'''
    def __init__(
        self: Self,
        name: str,
        help: str,
        transfer_method: str,
        file_mode: str,
        require_file: bool,
        support_sparse: bool = False,
        epilog: str | None = None,
        params: Sequence[click.Parameter] = [],
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        def cb(
            ctx: click.Context,
            state: State,
            target: Path,
            entity: str,
            parent: str | None = None,
            sparse: bool = False,
            **kwargs: Any,
        ) -> None:
            transfer_args = {k: v for k, v in kwargs.items()}
            transfer_args['sparse'] = sparse

            if require_file:
                if not target.exists():
                    LOGGER.error(f'{ str(target) } does not exist.')
                    ctx.exit(ExitCode.PATH_NOT_VALID)
            else:
                if not (target.parent.exists() and target.parent.is_dir()):
                    LOGGER.error(f'{ str(target.parent) } either does not exist or is not a directory.')
                    ctx.exit(ExitCode.PATH_NOT_VALID)

            if target.exists() and not (target.is_file() or target.is_block_device()):
                LOGGER.error(f'{ str(target) } must be a regular file or a block device.')
                ctx.exit(ExitCode.PATH_NOT_VALID)

            with state.hypervisor as hv:
                if self.HAS_PARENT:
                    assert parent is not None
                    assert self.PARENT_NAME is not None
                    obj = self.get_sub_entity(ctx, hv, parent, entity)
                else:
                    obj = self.get_entity(ctx, hv, entity)

                transfer = getattr(obj, transfer_method, None)

                if transfer is None:
                    raise RuntimeError

                with target.open(file_mode) as f:
                    try:
                        transferred = transfer(f, **transfer_args)
                    except OSError as e:
                        LOGGER.error(f'Operation failed due to local system error: { e.strerror }')
                        ctx.exit(ExitCode.OPERATION_FAILED)
                    except Exception as e:
                        LOGGER.error('Encountered unexpected error while trying to transfer data', exc_info=e)
                        ctx.exit(ExitCode.OPERATION_FAILED)

                click.echo(f'Finished transferring data, copied { state.convert_units(transferred) } of data.')
                ctx.exit(ExitCode.SUCCESS)

        params = tuple(params) + self.mixin_params(required=True) + (
            click.Argument(
                param_decls=('target',),
                metavar='FILE',
                nargs=1,
                required=True,
                type=click.Path(dir_okay=False, resolve_path=True, allow_dash=False, path_type=Path),
            ),
        )

        if support_sparse:
            params += (click.Option(
                param_decls=('--sparse',),
                is_flag=True,
                default=False,
                help='Skip holes when transferring data.',
            ),)

        super().__init__(
            name=name,
            help=help,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
