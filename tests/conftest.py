# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Test fixtures for fvirt'''

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from pathlib import Path
from traceback import format_exception
from typing import TYPE_CHECKING, Any

import pytest

from simple_file_lock import FileLock

from fvirt.cli import cli
from fvirt.libvirt import URI, Domain, Hypervisor, StoragePool, Volume
from fvirt.libvirt.events import start_libvirt_event_thread

if TYPE_CHECKING:
    from collections.abc import Sequence

    from click.testing import CliRunner, Result

XSLT_DATA = '''
<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl='http://www.w3.org/1999/XSL/Transform' version='1.0'>
    <xsl:output method='xml' encoding='utf-8'/>
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match='{path}/text()'>
        <xsl:text>{value}</xsl:text>
    </xsl:template>
</xsl:stylesheet>
'''.lstrip().rstrip()


@pytest.fixture
def runner(cli_runner: CliRunner) -> Callable[[Sequence[str], int], Result]:
    '''Provide a runner for running the fvirt cli with a given set of arguments.'''
    def runner(args: Sequence[str], exit_code: int) -> Result:
        result = cli_runner.invoke(cli, args)

        if isinstance(result.exception, SystemExit) and exit_code != 0:
            assert result.exit_code == exit_code, result.output
        else:
            assert not result.exception, ''.join(format_exception(*result.exc_info))  # type: ignore
            assert result.exit_code == exit_code, result.output

        return result

    return runner


@pytest.fixture(scope='session')
def xslt_doc_factory() -> Callable[[str, str], str]:
    '''Provide a callable that produces an XSLT document.

       The produced document will, when run through an XSLT processor,
       modify the path specified as the first argument to have the text
       specified as the second argument.'''
    def inner(path: str, value: str) -> str:
        return XSLT_DATA.format(path=path, value=value)

    return inner


@pytest.fixture(scope='session')
def libvirt_event_loop() -> None:
    '''Ensure that the libvirt event loop is running.'''
    start_libvirt_event_thread()
    return None


@pytest.fixture(scope='session')
def test_uri() -> str:
    '''Provide the libvirt URI to use for testing.'''
    return 'test:///default'


@pytest.fixture(scope='session')
def live_uri(libvirt_event_loop: None) -> str:
    '''Provide a live libvirt URI to use for testing.'''
    return 'qemu:///session'


@pytest.fixture(scope='session')
def lock_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    '''Provide a session-scoped lock directory.'''
    return tmp_path_factory.mktemp('lock')


@pytest.fixture
def serial(lock_dir: Path) -> Callable[[str], _GeneratorContextManager[None]]:
    '''Provide a callable to serialize parts of a test against other tests.'''
    @contextmanager
    def inner(path: str) -> Generator[None, None, None]:
        with FileLock(lock_dir / path):
            yield

    return inner


@pytest.fixture
def test_hv(test_uri: str) -> Hypervisor:
    return Hypervisor(hvuri=URI.from_string(test_uri))


@pytest.fixture
def live_hv(live_uri: str) -> Hypervisor:
    return Hypervisor(hvuri=URI.from_string(live_uri))


@pytest.fixture
def dom_xml(unique: Callable[..., Any]) -> Callable[[], str]:
    '''Provide a factory that produces domain XML strings.'''
    def inner() -> str:
        name = unique('text', prefix='fvirt-test')
        uuid = unique('uuid')

        return f'''
        <domain type='test'>
            <name>{ name }</name>
            <uuid>{ uuid }</uuid>
            <memory unit='MiB'>64</memory>
            <currentMemory unit='MiB'>32</currentMemory>
            <vcpu placement='static'>2</vcpu>
            <os>
                <type arch='x86_64'>hvm</type>
                <boot dev='hd' />
            </os>
            <clock offset='utc' />
            <devices>
                <disk type='file' device='disk'>
                    <source file='/guest/diskimage1'/>
                    <target dev='vda' bus='virtio'/>
                </disk>
                <interface type='network'>
                    <mac address='aa:bb:cc:dd:ee:ff'/>
                    <source network='default'/>
                    <target dev='testnet0'/>
                </interface>
                <memballoon model='virtio' />
            </devices>
        </domain>
        '''

    return inner


@pytest.fixture
def test_dom(
        test_hv: Hypervisor,
        dom_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]]
) -> Generator[Domain, None, None]:
    '''Provide a running Domain instance to operate on.

       Also ensures it's persistent.'''
    with serial('domain'):
        dom = test_hv.define_domain(dom_xml())

    dom.start()

    yield dom

    with serial('domain'):
        if dom.valid:
            dom.destroy(idempotent=True)
            dom.undefine()


@pytest.fixture
def pool_xml(unique: Callable[..., Any], tmp_path: Path) -> Callable[[], str]:
    '''Provide a factory function that produces storage pool XML strings.'''
    def inner() -> str:
        name = unique('text', prefix='fvirt-test')
        uuid = unique('uuid')
        path = tmp_path / name

        return f'''
        <pool type='dir'>
            <name>{ name }</name>
            <uuid>{ uuid }</uuid>
            <source />
            <target>
                <path>{ path }</path>
            </target>
        </pool>
        '''

    return inner


@pytest.fixture
def live_pool(
        live_hv: Hypervisor,
        pool_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]],
) -> Generator[StoragePool, None, None]:
    '''Provide a running StoragePool instance to operate on.

       Also ensures it's persistent.'''
    with serial('pool'):
        pool = live_hv.define_storage_pool(pool_xml())

    pool.build()
    pool.start()

    yield pool

    with serial('pool'):
        if pool.valid:
            pool.destroy(idempotent=True)
            pool.delete()
            pool.undefine()


@pytest.fixture
def test_pool(
        test_hv: Hypervisor,
        pool_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]]
) -> Generator[StoragePool, None, None]:
    '''Provide a running StoragePool instance to operate on.

       Also ensures it's persistent.'''
    with serial('pool'):
        pool = test_hv.define_storage_pool(pool_xml())

    pool.build()
    pool.start()

    yield pool

    with serial('pool'):
        if pool.valid:
            pool.destroy(idempotent=True)
            pool.delete()
            pool.undefine()


@pytest.fixture
def volume_xml(unique: Callable[..., Any]) -> Callable[[StoragePool, int], str]:
    '''Provide a function that, given a storage pool, will produce an XML string for a Volume.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool, size: int = 1024 * 1024) -> str:
        name = unique('text', prefix='fvirt-test')
        size = size
        path = Path(pool.target) / name

        return f'''
        <volume type='file'>
            <name>{ name }</name>
            <allocated units='bytes'>0</allocated>
            <capacity units='bytes'>{ size }</capacity>
            <target>
                <path>{ path }</path>
                <format type='raw' />
            </target>
        </volume>
        '''

    return inner


@pytest.fixture
def volume_factory(volume_xml: Callable[[StoragePool, int], str]) -> Callable[[StoragePool], Volume]:
    '''Provide a function that defines volumes given a storage pool, name, and size.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool, size: int = 1024 * 1024) -> Volume:
        return pool.define_volume(volume_xml(pool, size))

    return inner


@pytest.fixture
def test_volume(test_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> Generator[Volume, None, None]:
    '''Provide a test volume to operate on.'''
    vol = volume_factory(test_pool)

    assert '_hv' in dir(vol)

    yield vol

    assert '_hv' in dir(vol)

    if vol.valid:
        vol.undefine()


@pytest.fixture
def live_volume(live_pool: StoragePool, volume_factory: Callable[[StoragePool], Volume]) -> Generator[Volume, None, None]:
    '''Provide a live volume to operate on.'''
    vol = volume_factory(live_pool)

    assert '_hv' in dir(vol)

    yield vol

    assert '_hv' in dir(vol)

    if vol.valid:
        vol.undefine()
