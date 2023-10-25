# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for manipulating autostart status for objects.'''

from __future__ import annotations

from collections.abc import Mapping, Sequence
from textwrap import dedent
from typing import TYPE_CHECKING, Self, cast

import click

from .exitcode import ExitCode
from .match import MatchArgument, MatchCommand, get_match_or_entity
from .objects import is_object_mixin
from ...libvirt import InsufficientPrivileges
from ...libvirt.entity import RunnableEntity

if TYPE_CHECKING:
    from .state import State
    from ...util.match import MatchAlias


class AutostartCommand(MatchCommand):
    '''Class for commands that manipulate autostart state for objects.

       This provides the callback and all the other info required.'''
    def __init__(
        self: Self,
        name: str,
        aliases: Mapping[str, MatchAlias],
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        params = self.mixin_params() + (
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
                    obj=self,
                    hv=hv,
                    match=match,
                    entity=entity,
                    ctx=ctx,
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
                            ctx.fail(f'Cannot modify { self.NAME } autostart state as the Hypervisor connection is read-only.')

                        success += 1

                click.echo(f'Finished setting autostart status for specified { self.NAME }s.')
                click.echo('')
                click.echo('Results:')
                click.echo(f'  Success:     { success }')
                click.echo(f'  Failed:      { len(entities) - success }')

                if skipped:
                    click.echo(f'    Skipped:   { skipped }')

                click.echo(f'Total:         { len(entities) }')

                if success != len(entities) or (not entities and cli_state.fail_if_no_match):
                    ctx.exit(ExitCode.OPERATION_FAILED)

        docstr = dedent(f'''
        Set autostart state for one or more { self.NAME }s.

        To list the current autostart status for { self.NAME }s, use the
        'list' subcommand.

        Either a specific { self.NAME } to set the autostart state
        for should be specified as NAME, or matching parameters should
        be specified using the --match option, which will then cause
        all active { self.NAME }s that match to have their autostart
        state set.

        STATE should be one of 'on' or 'off' to enable or disable
        autostart functionality respectively. The integers 1 and 0 are
        also accepted with the same meanings.

        If more than one { self.NAME } is requested to have it's
        autostart state set, a failure setting the autostart state for
        any { self.NAME } will result in a non-zero exit code even if
        the autostart state was set successfully for some { self.NAME }s.

        This command does not support parallelization when operating on
        multiple { self.NAME }s. No matter how many jobs are requested,
        only one actual job will be used.

        This command does not support fvirt's fail-fast mode, as the only
        failures possible for this operation will cause the operation
        to fail for all { self.NAME }s.

        This command supports fvirt's idempotent mode. In idempotent mode,
        any { self.NAME }s which already have the desired autostart
        state will be treated as having their state successfully
        set.''').lstrip().rstrip()

        super().__init__(
            name=name,
            aliases=aliases,
            callback=cb,
            deprecated=deprecated,
            epilog=epilog,
            help=docstr,
            hidden=hidden,
            params=params,
        )
