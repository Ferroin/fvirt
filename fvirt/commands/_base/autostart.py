# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for manipulating autostart status for objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Self, cast

import click

from .match import MatchArgument, MatchCommand, get_match_or_entity
from ...libvirt import InsufficientPrivileges

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .state import State
    from ...libvirt.entity import RunnableEntity
    from ...util.match import MatchAlias


class AutostartCommand(MatchCommand):
    '''Class for commands that manipulate autostart state for objects.

       This provides the callback and all the other info required.'''
    def __init__(
        self: Self,
        name: str,
        aliases: Mapping[str, MatchAlias],
        hvprop: str,
        doc_name: str,
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        params = (
            click.Argument(
                param_decls=('entity',),
                nargs=1,
                default=None,
            ),
            click.Argument(
                param_decls=('state',),
                nargs=1,
                type=click.BOOL,
                required=True,
            ),
        )

        def cb(ctx: click.Context, cli_state: State, /, match: MatchArgument, entity: str | None, state: bool) -> None:
            with cli_state.hypervisor as hv:
                entities = cast(Sequence[RunnableEntity], get_match_or_entity(
                    hv=hv,
                    hvprop=hvprop,
                    match=match,
                    entity=entity,
                    ctx=ctx,
                    doc_name=doc_name,
                ))

                success = 0
                skipped = 0

                for e in entities:
                    if e.autostart == state:
                        skipped += 1
                        if cli_state.idempotent:
                            success += 1
                    else:
                        try:
                            e.autostart = state
                        except InsufficientPrivileges:
                            ctx.fail(f'Cannot modify { doc_name } autostart state as the Hypervisor connection is read-only.')

                        success += 1

                click.echo(f'Finished setting autostart status for specified { doc_name }s.')
                click.echo('')
                click.echo('Results:')
                click.echo(f'  Success:     { success }')
                click.echo(f'  Failed:      { len(entities) - success }')

                if skipped:
                    click.echo(f'    Skipped:   { skipped }')

                click.echo(f'Total:         { len(entities) }')

                if success != len(entities) or (not entities and cli_state.fail_if_no_match):
                    ctx.exit(3)

        docstr = dedent(f'''
        Set autostart state for one or more { doc_name }s.

        To list the current autostart status for { doc_name }s, use the
        'list' subcommand.

        Either a specific { doc_name } to set the autostart state for
        should be specified as NAME, or matching parameters should be
        specified using the --match option, which will then cause all
        active { doc_name }s that match to have their autostart state set.

        STATE should be one of 'on' or 'off' to enable or disable
        autostart functionality respectively. The integers 1 and 0 are
        also accepted with the same meanings.

        If more than one { doc_name } is requested to have it's autostart
        state set, a failure setting the autostart state for any {
        doc_name } will result in a non-zero exit code even if the
        autostart state was set successfully for some { doc_name }s.

        This command does not support fvirt's fail-fast mode, as the only
        failures possible for this operation will cause the operation
        to fail for all { doc_name }s.

        This command supports fvirt's idempotent mode. In idempotent
        mode, any { doc_name }s which already have the desired autostart
        state will be treated as having their state successfully
        set.''').lstrip().rstrip()

        super().__init__(
            aliases=aliases,
            callback=cb,
            deprecated=deprecated,
            doc_name=doc_name,
            epilog=epilog,
            help=docstr,
            hidden=hidden,
            name=name,
            params=params,
        )
