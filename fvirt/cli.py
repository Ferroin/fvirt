# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''CLI interface for fvirt.'''

from __future__ import annotations

import click

from .libvirt import API_VERSION, URI, Driver, Transport
from .version import VERSION
from .commands import COMMANDS
from .util.match import MATCH_HELP
from .util.commands import make_help_command

RECOGNIZED_DRIVERS = sorted(list({e.value for e in Driver}))
RECOGNIZED_TRANSPORTS = sorted(list({e.value for e in Transport if e.value}))

CONNECTION_HELP = click.wrap_text('''
fvirt uses standard libvirt connection URI syntax, just like virsh and
most other libvirt frontends do. Actual connection handling is done by
libvirt itself, not fvirt, so barring the case of fvirt not recognizing
a driver or transport, any valid libvirt URI should just work.

When run without an explicit --connect option (or if an empty string
is given to the --connect option), fvirt leverages libvirt’s existing
default URI selection logic. Because this logic is provided by libvirt
itself, fvirt should use the exact same default URI in any given situation
that would be used by virsh, virt-manager, and virt-install.

fvirt does not (currently) support URI aliases.
'''.lstrip().rstrip(), preserve_paragraphs=True)

CONNECTION_HELP += f'\n\nSupported drivers:\n{ click.wrap_text(" ".join(RECOGNIZED_DRIVERS), initial_indent="  ", subsequent_indent="  ") }'
CONNECTION_HELP += f'\n\nSupported transports:\n{ click.wrap_text(" ".join(RECOGNIZED_TRANSPORTS), initial_indent="  ", subsequent_indent="  ") }'


@click.group
@click.version_option(version=f'{ VERSION }, using libvirt-python { API_VERSION }')
@click.option('--connect', '-c', '--uri', nargs=1, type=str, default='',
              help='Specify the hypervisor connection URI', metavar='URI')
@click.option('--fail-fast/--no-fail-fast', default=False,
              help='If operating on multiple objects, fail as soon as one operation fails instead of attempting all operations.')
@click.option('--idempotent/--no-idempotent', default=True,
              help='Make operations idempotent when possible.')
@click.option('--fail-if-no-match/--no-fail-if-no-match', default=False,
              help='If using the --match option, return with a non-zero exit status if no match is found.')
@click.pass_context
def cli(
        ctx: click.core.Context,
        connect: str,
        fail_fast: bool,
        idempotent: bool,
        fail_if_no_match: bool,
        ) -> None:
    '''A lightweight frontend for libvirt.

       Most commands are grouped by the type of libvirt object they
       operate on.

       For more information about a specific command, run that `fvirt
       help <command>`.'''
    ctx.max_content_width = 80
    ctx.ensure_object(dict)
    ctx.obj['uri'] = URI.from_string(connect)
    ctx.obj['fail_fast'] = fail_fast
    ctx.obj['idempotent'] = idempotent
    ctx.obj['fail_if_no_match'] = fail_if_no_match


for cmd in COMMANDS:
    cli.add_command(cmd)

cli.add_command(make_help_command(cli, 'fvirt', {
    'matching': (
        'Information about fvirt object matching syntax.',
        click.wrap_text(MATCH_HELP, preserve_paragraphs=True),
    ),
    'connections': (
        'Information about how fvirt handles hypervisor connections.',
        CONNECTION_HELP,
    ),
}))

__all__ = [
    'cli',
]
