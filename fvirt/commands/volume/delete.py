# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to delete volumes.'''

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import click

from .._base.match import MatchArgument, MatchCommand, get_match_or_entity
from ...libvirt import LifecycleResult
from ...libvirt.volume import MATCH_ALIASES, Volume

if TYPE_CHECKING:
    from .._base.state import State

HELP = '''
Delete one or more volumes from the specified storage pool.

The POOL argument should indicate which storage pool to delete the
volumes from.

Either a specific volume name to delete should be specified as NAME,
or matching parameters should be specified using the --match option,
which will then cause all active volumes that match to be deleted.

If more than one volume is requested to be deleted, a failure deleting
any volume will result in a non-zero exit code even if some volumes
were deleted.

This command supports fvirt's fail-fast logic. In fail-fast mode, the
first volume that fails to be deleted will cause the operation to stop,
and any failure will result in a non-zero exit code.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State, pool: str, match: MatchArgument, entity: str | None) -> None:
    with state.hypervisor as hv:
        parent = hv.pools.get(pool)

        if parent is None:
            ctx.fail(f'No storage pool found with name or UUID equal to { pool }.')

        entities = cast(Sequence[Volume], get_match_or_entity(
            hv=parent,
            hvprop='volumes',
            match=match,
            entity=entity,
            ctx=ctx,
            doc_name='volume',
        ))

        success = 0
        skipped = 0

        for e in entities:
            match e.delete(idempotent=state.idempotent):
                case LifecycleResult.SUCCESS:
                    click.echo(f'Deleted volume "{ e.name }".')
                    success += 1
                case LifecycleResult.NO_OPERATION:
                    click.echo(f'Volume "{ e.name }" does not exist.')
                    skipped += 1

                    if state.idempotent:
                        success += 1
                case LifecycleResult.FAILURE:
                    click.echo(f'Failed to delte volume "{ e.name }".')

                    if state.fail_fast:
                        break

    click.echo('Finished deleting specified volumes.')
    click.echo('')
    click.echo('Results:')
    click.echo(f'  Success:     { success }')
    click.echo(f'  Failed:      { len(entities) - success }')

    if skipped:
        click.echo(f'    Skipped:   { skipped }')

    click.echo(f'Total:         { len(entities) }')

    if success != len(entities) or (not entities and state.fail_if_no_match):
        ctx.exit(3)


delete = MatchCommand(
    name='delete',
    help=HELP,
    aliases=MATCH_ALIASES,
    callback=cb,
    doc_name='volume',
    params=(
        click.Argument(
            param_decls=('pool',),
            nargs=1,
            required=True,
        ),
        click.Argument(
            param_decls=('volume',),
            nargs=1,
        ),
    ),
)

__all__ = [
    'delete',
]
