# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to gracefully shut down domains.'''

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import click

from ...libvirt import Hypervisor, Domain, LifecycleResult
from ...libvirt.domain import MATCH_ALIASES
from ...util.commands import get_match_or_entity, add_match_options

if TYPE_CHECKING:
    import re

    from ...util.match import MatchTarget


@click.command(name='shutdown')
@add_match_options(MATCH_ALIASES, 'domain')
@click.option('--timeout', type=click.IntRange(min=0), default=0,
              help='Specify a timeout in seconds within which the domain must shut down. A value of 0 means no timeout.')
@click.option('--force', is_flag=True, default=False,
              help='If a domain fails to shut down within the specified timeout, forcibly stop it.')
@click.argument('name', nargs=1, required=False)
@click.pass_context
def shutdown(
        ctx: click.core.Context,
        match: tuple[MatchTarget, re.Pattern] | None,
        timeout: int,
        force: bool,
        name: str | None,
        ) -> None:
    '''Gracefully shut down one or more running domains.

       Either a specific domain name to shut down should be specified
       as NAME, or matching parameters should be specified using the
       --match option, which will then cause all running domains that
       are matched to be shut down.

       If more than one domain is requested to be shut down, a failure
       resetting any domain will result in a non-zero exit code even if
       some domains were started.

       If a timeout is specified, it is applied for each domain that is
       being shut down. For example, if you use `--match` and it matches
       three domains, and have a timeout of 20 seconds, then it may take
       up to 60 seconds to shut down all the domains.

       This command supports fvirt's fail-fast logic. In fail-fast mode,
       the first domain that fails to be reset will cause the operation to
       stop, and any failure will result in a non-zero exit code.

       This command supports fvirt's idempotent logic. In idempotent
       mode, failing to shut down a domain because it is not running
       will not be treated as an error.'''
    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        entities = cast(Sequence[Domain], get_match_or_entity(
            hv=hv,
            hvprop='domains',
            hvnameprop='domains_by_name',
            match=match,
            entity=name,
            ctx=ctx,
            doc_name='domain',
        ))

        success = 0
        skipped = 0
        timed_out = 0

        for e in entities:
            match e.shutdown(timeout=timeout, force=force, idempotent=ctx.obj['idempotent']):
                case LifecycleResult.SUCCESS:
                    click.echo(f'Shut down domain "{ e.name }".')
                    success += 1
                case LifecycleResult.FAILURE:
                    click.echo(f'Failed to shut down domain "{ e.name }".')

                    if ctx.obj['fail_fast']:
                        break
                case LifecycleResult.NO_OPERATION:
                    click.echo(f'Domain "{ e.name }" is not running, and thus cannot be shut down.')

                    skipped += 1

                    if ctx.obj['fail_fast']:
                        break
                case LifecycleResult.TIMED_OUT:
                    click.echo(f'Timed out while waiting for domain "{ e.name }" to shut down.')

                    timed_out += 1

                    if ctx.obj['fail_fast']:
                        break
                case LifecycleResult.FORCED:
                    click.echo(f'Timed out while waiting for domain "{ e.name }" to shut down, domain shut down forcibly.')

                    success += 1
                    timed_out += 1
                case _:
                    raise RuntimeError

        if success or (not entities and not ctx.obj['fail_if_no_match']):
            click.echo(
                f'Successfully shut down { success } out of { len(entities) } domains ({ skipped } already shut off, { timed_out } timed out).'
            )

            if success != len(entities) and ctx.obj['fail_fast']:
                ctx.exit(3)
        else:
            click.echo('Failed to shut down any domains.')
            ctx.exit(3)


__all__ = [
    'shutdown',
]
