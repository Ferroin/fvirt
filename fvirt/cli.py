# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''CLI interface for fvirt.'''

from __future__ import annotations

from pathlib import Path
from typing import Final, Literal

import click

from .commands import LAZY_COMMANDS
from .commands._base.config import CONFIG_PATHS
from .commands._base.group import Group
from .commands._base.help import HelpTopic
from .commands._base.state import DEFAULT_JOB_COUNT, State
from .libvirt.uri import URI, Driver, Transport
from .util.match import MATCH_HELP

RECOGNIZED_DRIVERS: Final = sorted(list({e.value for e in Driver}))
RECOGNIZED_TRANSPORTS: Final = sorted(list({e.value for e in Transport if e.value}))

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

CONCURRENCY_HELP = f'''
When asked to perform an operation on more than one libvirt object,
fvirt will usually attempt to parallelize the operations using a thread
pool to speed up processing.

By default, this thread pool will use either 8 threads, or four more
threads than the number of CPUs in the systme, whichever is less. If
fvirt determines that it is restricted to a subset of the number of
logical CPUs in the system, that subset will be treated as the number
of CPUs in the system for determining the number of threads to use.

If fvirt cannot determine the number of CPUs in the system, fvirt will
default to using 8 threads.

Operations on single objects will completely bypass the thread pool.

Some commands will bypass the thread pool even if asked to operate on
multiple objects. They will explicitly state this in their help text.

The number of threads to be used can be overridden using the `--jobs`
option. A value of 0 explicitly requests the default number of jobs and
will override any value specified in the config file. A value of 1 will
run everything sequentially.

The default number of jobs on this system is { DEFAULT_JOB_COUNT }.
'''.lstrip().rstrip()

UNITS_HELP = '''
fvirt supports three different modes when printing a number indicating
a count of bytes:

- 'raw' or 'bytes' mode
- 'si' mode
- 'iec' mode

The 'raw' mode simply displays the total number of bytes as an
integer. This is provided to allow other tools to more easily parse
fvirt's output.

The other two modes convert the raw number of bytes to a larger unit
such that there are between one and four digits to the left of the
decimal point, with the largest supported unit currently being
exabytes/ebibytes. Between zero and three digits will be provided after
the decimal point depending on how many digits preceed it.

The 'si' mode uses official SI units based on every third power of ten,
with the special exception that the `k` for kilobytes is capitalized
for consistency with libvirt’s own unit representations.

The `iec` mode uses IEC units based on every tenth power of two. These
units are more common in the context of computers.

By default, fvirt will display units using the 'si' mode.
'''.lstrip().rstrip()

CONFIG_PATH_LIST = f'Configuration search paths: {", ".join([str(x) for x in CONFIG_PATHS])}'

CONFIGURATION_HELP = f'''
fvirt supports loading a configuration file to provide default values
for a number of runtime configurable aspects of it's behavior.

A specific configuration file may be specified manually using the
--config-file option. If a configuration is manually specified, but the
requested file does not exist, fvirt will exit with an error without
doing anything. If a configuration is not manually specified, fvirt will
instead search a set of platform specific locations and use the first
file it finds among those locations. If no configuration file is found,
internal defaults will be used instead.

Configuration may be provided both as global defaults, and as URI-specific
overrides, with the URI-specific configurations taking precedence over
the global defaults, and options specified on the command line always
overriding any configuration in the configuration file.

The configuration file format is YAML. The full configuration schema
can be viewed by running 'fvirt schema config'.

{CONFIG_PATH_LIST}
'''.lstrip().rstrip()

FVIRT_HELP = '''
A command-line frontend for libvirt.

Most commands are grouped by the type of libvirt object they operate on.

For more information about a specific command, run `fvirt help COMMAND`.
'''.lstrip().rstrip()


def cb(
    ctx: click.Context,
    connect: str,
    fail_fast: bool | None,
    idempotent: bool | None,
    fail_if_no_match: bool | None,
    units: str | None,
    jobs: int | None,
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] | None,
    config_file: Path | None,
) -> None:
    ctx.obj = State(
        config_file=config_file,
        uri=URI.from_string(connect),
        fail_fast=fail_fast,
        idempotent=idempotent,
        fail_if_no_match=fail_if_no_match,
        units=units,
        jobs=jobs,
        log_level=log_level,
    )


cli: Final = Group(
    name='fvirt',
    help=FVIRT_HELP,
    callback=cb,
    lazy_commands=LAZY_COMMANDS,
    params=(
        click.Option(
            param_decls=('--connect', '-c', '--uri'),
            type=str,
            default='',
            help='Specify the libvirt connection URI to use.',
            metavar='URI',
        ),
        click.Option(
            param_decls=('--config-file',),
            type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, allow_dash=False, path_type=Path),
            default=None,
            nargs=1,
            help='Specify an alternative configuration file to use.',
        ),
        click.Option(
            param_decls=('--fail-fast/--no-fail-fast',),
            default=None,
            help='If operating on multiple objects, fail as soon as one operation fails instead of attempting all operations.',
        ),
        click.Option(
            param_decls=('--idempotent/--no-idempotent',),
            default=None,
            help='Make operations idempotent when possible. Enabled by default.',
        ),
        click.Option(
            param_decls=('--fail-if-no-match/--no-fail-if-no-match',),
            default=None,
            help='If using the --match option, return with a non-zero exist status if no match is found.',
        ),
        click.Option(
            param_decls=('--units',),
            default=None,
            type=click.Choice(('raw', 'bytes', 'si', 'iec'), case_sensitive=False),
            help='Indicate how units should be printed. See `fvirt help units` for more info.',
        ),
        click.Option(
            param_decls=('--jobs', '-j'),
            default=None,
            type=click.IntRange(min=0),
            help='Specify the number of jobs to use for concurrent execution. Run `fvirt help concurrency` for more information.',
        ),
        click.Option(
            param_decls=('--log-level', '-l'),
            default=None,
            type=click.Choice(('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'), case_sensitive=False),
            help='Specify the lowest level of log messages to display.',
        ),
    ),
    help_topics=(
        HelpTopic(
            name='config',
            description='Information about fvirt configuration files.',
            help_text=CONFIGURATION_HELP,
        ),
        HelpTopic(
            name='matching',
            description='Information about fvirt object matcing syntax.',
            help_text=click.wrap_text(MATCH_HELP, preserve_paragraphs=True),
        ),
        HelpTopic(
            name='connections',
            description='Information about how fvirt handles hypervisor connections.',
            help_text=CONNECTION_HELP,
        ),
        HelpTopic(
            name='concurrency',
            description="Information about fvirt's concurrent processing functionality.",
            help_text=CONCURRENCY_HELP,
        ),
        HelpTopic(
            name='units',
            description='Information about how fvirt handles units when displaying byte values.',
            help_text=UNITS_HELP,
        ),
    ),
)

__all__ = [
    'cli',
]
