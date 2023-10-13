# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to delete volumes.'''

from __future__ import annotations

import concurrent.futures

from typing import TYPE_CHECKING

import click

from .._base.match import MatchArgument, MatchCommand, get_match_or_entity
from ...libvirt import LifecycleResult
from ...libvirt.runner import RunnerResult, run_sub_entity_method
from ...libvirt.volume import MATCH_ALIASES

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

This command supports fvirt's idempotent logic. In idempotent mode,
failing to delete a volume because it is does not exist will not be
treated as an error.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State, pool: str, match: MatchArgument, entity: str | None) -> None:
    with state.hypervisor as hv:
        parent = hv.pools.get(pool)

        if parent is None:
            ctx.fail(f'No storage pool found with name or UUID equal to { pool }.')

        futures = [state.pool.submit(
            run_sub_entity_method,
            uri=hv.uri,
            hvprop='pools',
            parentprop='volumes',
            method='delete',
            ident=(parent.name, e.name),
        ) for e in get_match_or_entity(
            hv=parent,
            hvprop='volumes',
            match=match,
            entity=entity,
            ctx=ctx,
            doc_name='volume',
        )]

    success = 0
    skipped = 0

    for f in concurrent.futures.as_completed(futures):
        match f.result():
            case RunnerResult(attrs_found=False) as r:
                ctx.fail(f'Unexpected internal error processing volume "{ r.ident[1] }".')
            case RunnerResult(entity_found=False) as r:
                click.echo(f'Storage pool "{ r.ident[0] }" disappeared while trying to process volumes in it.')
                break  # Not recoverable, but we still need to show the summary.
            case RunnerResult(entity_found=True, sub_entity_found=False) as r:
                click.echo(f'Volume "{ r.ident[1] }" disappeared before we could delete it.')

                if state.fail_fast:
                    break
            case RunnerResult(method_success=False) as r:
                click.echo(f'Unexpected error processing volume "{ r.ident }".')

                if state.fail_fast:
                    break
            case RunnerResult(method_success=True, result=LifecycleResult.SUCCESS):
                click.echo(f'Deleted volume "{ r.ident[1] }".')
                success += 1
            case RunnerResult(method_success=True, result=LifecycleResult.NO_OPERATION):
                click.echo(f'Volume "{ r.ident[1] }" is already deleted.')
                skipped += 1

                if state.idempotent:
                    success += 1
            case RunnerResult(method_success=True, result=LifecycleResult.FAILURE):
                click.echo(f'Failed to delete volume "{ r.ident[1] }".')

                if state.fail_fast:
                    break
            case _:
                raise RuntimeError

    click.echo('Finished deleting specified volumes.')
    click.echo('')
    click.echo('Results:')
    click.echo(f'  Success:     { success }')
    click.echo(f'  Failed:      { len(futures) - success }')

    if skipped:
        click.echo(f'    Skipped:   { skipped }')

    click.echo(f'Total:         { len(futures) }')

    if success != len(futures) or (not futures and state.fail_if_no_match):
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
