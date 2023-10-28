# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to access a console device of a domain.'''

from __future__ import annotations

import codecs
import sys

from typing import TYPE_CHECKING, Final, Self, cast, final

import click

from .._base.command import Command
from .._base.exitcode import ExitCode
from .._base.objects import DomainMixin
from ...libvirt.domain import Domain
from ...util.terminal import get_terminal

if TYPE_CHECKING:
    from .._base.state import State

# The IO loop we use for relaying data between the console and the libvirt
# stream intentionally limits the amount of data read from libvirt in one
# pass and the amount of time we wait for a keypress from the user to
# ensure responsiveness on both input and output.
#
# READ_MAX is the largest amount of bytes we grab from libvirt at once. 32
# kiB is sufficient for a very _very_ large console, and actually probably
# overkill for normal usage.
#
# WRITE_WAIT is how long we wait for user input before continuing the
# loop. 5ms is good enough in most cases, especially considering that we
# read one input at a time but the individual inputs are buffered.
READ_MAX = 32768
WRITE_WAIT = 0.005

DEFAULT_ENCODING = 'utf8'

HELP: Final = '''
Connect to a domain console (or other character device).

DOMAIN specifies the domain to connect to.

Use ^] (Ctrl + ] on most keyboards) to disconnect. The console will
be disconnected automatically if the domain shuts down, or some other
process attempts to connect to the same console.

You will generally need to ensure that the encoding used by the guest
OS matches what fvirt tries to use when decoding things. Unless told
otherwise, fvirt will assume the guest is configured to use UTF-8,
because this will be correct a significant majority of the time, and
even if it isn’t it will often still ‘just work’.

fvirt will do everything it can to avoid losing user input, but will
also try to avoid pending user input preventing output from being
printed either. This means that keystrokes may not arrive at the domain
immediately if libvirt is slow processing them for some reason.

This command does not support fvirt's fail-fast mode, as it does not
make sense for this operation.

This command does not support fvirt's idempotent mode, as it does not
make sense for this operation.
'''.lstrip().rstrip()


@final
class _ConsoleCommand(Command, DomainMixin):
    '''Command for accessing the domain console.'''
    def __init__(
        self: Self,
        name: str,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        def cb(
            ctx: click.Context,
            state: State,
            domain: str,
            encoding: str,
            dev: str | None,
            force: bool,
            safe: bool,
        ) -> None:
            terminal = get_terminal()
            done = False
            wbuf = b''

            try:
                codec = codecs.lookup(encoding)
            except LookupError:
                click.echo(f'"{ encoding }" is not a recognized encoding.', err=True)
                ctx.exit(ExitCode.BAD_ARGUMENTS)

            decode = codec.incrementaldecoder(errors='replace').decode
            encode = codec.incrementalencoder(errors='replace').encode

            with state.hypervisor as hv:
                dom = cast(Domain, self.get_entity(ctx, hv, domain))

                st = dom.console(dev, force=force, safe=safe)

                with terminal.fullscreen():
                    click.echo(f'Connected to domain "{ dom.name }"')
                    click.echo('Exit with ^] (Ctrl + ])')

                    with terminal.cbreak():
                        while dom.running and not done:
                            try:
                                rdata = st.read(READ_MAX)
                            except BlockingIOError:
                                pass
                            else:
                                sys.stdout.write(decode(rdata))

                            key = terminal.inkey(timeout=WRITE_WAIT)

                            if key == '\x1b':
                                done = True
                            else:
                                wbuf += encode(key)

                                try:
                                    st.write(wbuf)
                                except BlockingIOError:
                                    pass
                                else:
                                    wbuf = b''
                                    break

                if dom.running:
                    click.echo(f'Disconnected from domain "{ dom.name }"')
                else:
                    click.echo(f'Domain "{ dom.name }" has shut down.')

        params = self.mixin_params() + (
            click.Option(
                param_decls=('--device',),
                nargs=1,
                metavar='DEV',
                help='Specify a device to connect to other than the default console.',
            ),
            click.Option(
                param_decls=('--encoding',),
                default=DEFAULT_ENCODING,
                metavar='ENCODING',
                help='Specify what encoding to use when transfering data to/from the domain.',
            ),
            click.Option(
                param_decls=('--force/--no-force',),
                default=False,
                help='Force connecting to the console, disconnecting any already connected sessions.',
            ),
            click.Option(
                param_decls=('--safe',),
                is_flag=True,
                default=False,
                help='Only connect if safe console handling is supported.',
            ),
        )

        super().__init__(
            name=name,
            help=HELP,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )


console = _ConsoleCommand(
    name='console',
)

__all__ = (
    'console',
)
