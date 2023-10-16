# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to host info .'''

from __future__ import annotations

from typing import Final

import click

from .._base.command import Command
from .._base.state import State

HELP: Final = '''
Print information about the host system that fvirt is connected to.
'''.lstrip().rstrip()


def cb(ctx: click.Context, state: State) -> None:
    with state.hypervisor as hv:
        info = hv.host_info
        host = hv.hostname

    output = f'Hostname: { host }\n'
    output += f'CPU Architecture: { info.architecture }\n'
    output += f'Usable Memory: { info.memory }\n'
    output += f'Active CPUs: { info.cpus }\n'
    output += f'CPU Frequency: { info.cpu_frequency } MHz\n'
    output += f'NUMA Nodes: { info.nodes }\n'
    output += f'CPU Sockets per Node: { info.sockets }\n'
    output += f'CPU Cores per Socket: { info.cores }\n'
    output += f'CPU Threads per Core: { info.threads }'

    click.echo(output)


info: Final = Command(
    name='info',
    help=HELP,
    callback=cb,
)

__all__ = [
    'info',
]
