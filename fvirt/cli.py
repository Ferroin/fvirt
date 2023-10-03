# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''CLI interface for fvirt.'''

from __future__ import annotations

import click

from .commands import COMMANDS
from .commands._base.group import Group
from .commands._base.help import HelpTopic
from .libvirt import API_VERSION, URI, Driver, Transport
from .util.match import MATCH_HELP
from .version import VERSION

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

FVIRT_HELP = '''
A lightweight frontend for libvirt.

Most commands are grouped by the type of libvirt object they
operate on.

For more information about a specific command, run that `fvirt
help COMMAND`.
'''.lstrip().rstrip()


def cb(
        ctx: click.Context,
        connect: str,
        fail_fast: bool,
        idempotent: bool,
        fail_if_no_match: bool,
        version: bool,
        ) -> None:
    if version:
        click.echo(f'fvirt { VERSION }, using libvirt-python { API_VERSION }')
        ctx.exit(0)

    ctx.ensure_object(dict)
    ctx.obj['uri'] = URI.from_string(connect)
    ctx.obj['fail_fast'] = fail_fast
    ctx.obj['idempotent'] = idempotent
    ctx.obj['fail_if_no_match'] = fail_if_no_match


cli = Group(
    name='fvirt',
    help=FVIRT_HELP,
    callback=cb,
    commands=COMMANDS,
    params=(
        click.Option(
            param_decls=('--connect', '-c', '--uri'),
            type=str,
            default='',
            help='Specify the libvirt connection URI to use.',
            metavar='URI',
        ),
        click.Option(
            param_decls=('--fail-fast/--no-fail-fast',),
            default=False,
            help='If operating on multiple objects, fail as soon as one operation fails instead of attempting all operations.',
        ),
        click.Option(
            param_decls=('--idempotent/--no-idempotent',),
            default=True,
            help='Make operations idempotent when possible. Enabled by default.',
        ),
        click.Option(
            param_decls=('--fail-if-no-match/--no-fail-if-no-match',),
            default=False,
            help='If using the --match option, return with a non-zero exist status if no match is found.',
        ),
        click.Option(
            param_decls=('--version', '-V'),
            is_flag=True,
            default=False,
            help='Print the fvirt version.',
        ),
    ),
    help_topics=(
        HelpTopic(
            name='matching',
            description='Information about fvirt object matcing syntax',
            help_text=click.wrap_text(MATCH_HELP, preserve_paragraphs=True),
        ),
        HelpTopic(
            name='connections',
            description='Information about how fvirt handles hypervisor connections.',
            help_text=CONNECTION_HELP,
        ),
    ),
)

__all__ = [
    'cli',
]
