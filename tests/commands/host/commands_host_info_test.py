# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.host.info'''

from __future__ import annotations

import re

from socket import gethostname
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result


TEST_LINES = {
    'cpus': re.compile(r'Active CPUs: [0-9]*?$'),
}


def test_info_output(runner: Callable[[Sequence[str], int], Result], test_uri: str) -> None:
    '''Test that the command runs correctly.'''
    result = runner(('-c', test_uri, 'host', 'info'), 0)
    assert len(result.output.splitlines()) == 9

    hostname = re.search(r'^Hostname: ([a-zA-Z0-9][a-zA-Z0-9-]*?)$', result.output, re.MULTILINE)
    assert hostname, 'hostname information not found in output'
    assert hostname[1] == gethostname()

    architecture = re.search(r'^CPU Architecture: \w+?$', result.output, re.MULTILINE)
    assert architecture, 'CPU architecture information not found in output'

    memory = re.search(r'^Usable Memory: ([0-9]+?)$', result.output, re.MULTILINE)
    assert memory, 'usable memory not found in output'
    assert int(memory[1]) > 0

    cpus = re.search(r'^Active CPUs: ([0-9]+?)$', result.output, re.MULTILINE)
    assert cpus, 'active cpus not found in output'
    assert int(cpus[1]) > 0

    cpufreq = re.search(r'^CPU Frequency: ([0-9]+?) MHz$', result.output, re.MULTILINE)
    assert cpufreq, 'cpu frequency not found in output'
    assert int(cpufreq[1]) > 0

    nodes = re.search(r'^NUMA Nodes: ([0-9]+?)$', result.output, re.MULTILINE)
    assert nodes, 'numa nodes not found in output'
    assert int(nodes[1]) > 0

    sockets = re.search(r'^CPU Sockets per Node: ([0-9]+?)$', result.output, re.MULTILINE)
    assert sockets, 'cpu sockets not found in output'
    assert int(sockets[1]) > 0

    cores = re.search(r'^CPU Cores per Socket: ([0-9]+?)$', result.output, re.MULTILINE)
    assert cores, 'cpu cores not found in output'
    assert int(cores[1]) > 0

    threads = re.search(r'^CPU Threads per Core: ([0-9]+?)$', result.output, re.MULTILINE)
    assert threads, 'cpu threads not found in output'
    assert int(threads[1]) > 0
