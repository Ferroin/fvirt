# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Test fixtures for fvirt'''

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from pathlib import Path
from textwrap import dedent
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

        if isinstance(result.exception, SystemExit):
            if exit_code != 0:
                assert result.exit_code == exit_code, result.output
            else:
                assert False, result.output
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
def name_factory(unique: Callable[..., str], worker_id: str) -> Callable[[], str]:
    '''Provide a factory function for creating names for objects.'''
    def inner() -> str:
        return unique('text', prefix=f'fvirt-test-{worker_id}')

    return inner


@pytest.fixture(scope='session')
def libvirt_event_loop() -> None:
    '''Ensure that fvirt's libvirt event loop is running.'''
    start_libvirt_event_thread()
    return None


@pytest.fixture(scope='session')
def test_uri() -> str:
    '''Provide a libvirt URI to use for testing.'''
    return 'test:///default'


@pytest.fixture(scope='session')
def live_uri() -> str:
    '''Provide a live libvirt URI to use for testing.'''
    return 'qemu:///session'


@pytest.fixture
def embed_uri(tmp_path: Path) -> str:
    '''Provide an embedded QEMU libvirt URI to use for testing.'''
    return f'qemu:///embed?root={str(tmp_path)}'


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
    '''Provide a fvirt.libvirt.Hypervisor instance for testing.

       The provided instance will utilize the libvirt test driver with
       the default configuration, making it suitble for cases where
       interaction with live resources is not required.

       Because of how the test driver works, tests using this fixture
       do not need to worry about other tests accessing the hypervisor
       concurrently with them, but they do need to account for the
       possibility that the state exposed is not a clean instance of
       the test driver.'''
    return Hypervisor(hvuri=URI.from_string(test_uri))


@pytest.fixture
def live_hv(live_uri: str, libvirt_event_loop: None) -> Hypervisor:
    '''Provide a fvirt.libvirt.Hypervisor instance for testing.

       The provided instance will utilize the libvirt QEMU driver in
       session mode, making it suitable for cases that cannot be tested
       with either the test driver or an embedded QEMU driver, such as
       storage volume handling.

       This fixture may spawn an instance of libvirtd or virtqemud for
       the user running the tests if there is not one already running.

       Because this connects to a shared instance of libvirtd, test cases
       and fixtures that use this fixture should be written in such a
       way that they are safe against concurrent access and usage of
       the hypervisor, and should also make no assumptions about the
       initial state of the hypervisor.'''
    return Hypervisor(hvuri=URI.from_string(live_uri))


@pytest.fixture
def embed_hv(embed_uri: str, libvirt_event_loop: None) -> Hypervisor:
    '''Provide a fvirt.libvirt.Hypervisor instance for testing.

       The provided instance will utilize the libvirt QEMU driver in
       embedded mode with a unique root prefix, making it suitable for
       cases that require testing of actual, live, domains.

       Unlike the other hypervisor fixtures, this instance is guaranteed
       to be in a clean, well-defined state for each test and fixture
       that uses it and is safe against concurrent access, but it only
       supports working with domains.'''
    return Hypervisor(hvuri=URI.from_string(embed_uri))


@pytest.fixture
def dom_xml(unique: Callable[..., Any], name_factory: Callable[[], str]) -> Callable[[], str]:
    '''Provide a factory that produces domain XML strings.'''
    def inner() -> str:
        name = name_factory()
        uuid = unique('uuid')

        return dedent(f'''<domain type='test'>
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
        ''').lstrip().rstrip()

    return inner


@pytest.fixture
def test_dom(
        test_hv: Hypervisor,
        dom_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]]
) -> Generator[tuple[Domain, Hypervisor], None, None]:
    '''Provide a running, persistent Domain instance to operate on.

       Yields the domain instance and the associated Hypervisor instance
       in a tuple..'''
    with serial('test-domain'):
        dom = test_hv.define_domain(dom_xml())

    dom.start()
    uuid = dom.uuid

    yield (dom, test_hv)

    with serial('test-domain'):
        if test_hv.domains.get(uuid) is not None:
            dom.destroy(idempotent=True)
            dom.undefine()


@pytest.fixture
def pool_xml(unique: Callable[..., Any], tmp_path: Path, name_factory: Callable[[], str]) -> Callable[[], str]:
    '''Provide a factory function that produces storage pool XML strings.'''
    def inner() -> str:
        name = name_factory()
        uuid = unique('uuid')
        path = tmp_path / name

        return dedent(f'''<pool type='dir'>
            <name>{ name }</name>
            <uuid>{ uuid }</uuid>
            <source />
            <target>
                <path>{ path }</path>
            </target>
        </pool>
        ''').lstrip().rstrip()

    return inner


@pytest.fixture
def live_pool(
        live_hv: Hypervisor,
        pool_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]],
) -> Generator[tuple[StoragePool, Hypervisor], None, None]:
    '''Provide a running, persistent StoragePool instance to operate on.

       Yields a tuple of the StoragePool instance and the associated
       Hypervisor instance.'''
    with serial('live-pool'):
        pool = live_hv.define_storage_pool(pool_xml())

    pool.build()
    pool.start()

    uuid = pool.uuid

    yield (pool, live_hv)

    with serial('live-pool'):
        if live_hv.storage_pools.get(uuid) is not None:
            pool.destroy(idempotent=True)
            pool.delete()
            pool.undefine()


@pytest.fixture
def test_pool(
        test_hv: Hypervisor,
        pool_xml: Callable[[], str],
        serial: Callable[[str], _GeneratorContextManager[None]]
) -> Generator[tuple[StoragePool, Hypervisor], None, None]:
    '''Provide a running, persistent StoragePool instance to operate on.

       Yields a tuple of the StoragePool instance and the associated
       Hypervisor instance.'''
    with serial('test-pool'):
        pool = test_hv.define_storage_pool(pool_xml())

    pool.build()
    pool.start()

    uuid = pool.uuid

    yield (pool, test_hv)

    with serial('test-pool'):
        if test_hv.storage_pools.get(uuid) is not None:
            pool.destroy(idempotent=True)
            pool.delete()
            pool.undefine()


@pytest.fixture
def volume_xml(name_factory: Callable[[], str]) -> Callable[[StoragePool, int], str]:
    '''Provide a function that, given a storage pool, will produce an XML string for a Volume.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool, size: int = 1024 * 1024) -> str:
        name = name_factory()
        size = size
        path = Path(pool.target) / name

        return dedent(f'''
        <volume type='file'>
            <name>{ name }</name>
            <allocated units='bytes'>0</allocated>
            <capacity units='bytes'>{ size }</capacity>
            <target>
                <path>{ path }</path>
                <format type='raw' />
            </target>
        </volume>
        ''').lstrip().rstrip()

    return inner


@pytest.fixture
def volume_factory(volume_xml: Callable[[StoragePool, int], str]) -> Callable[[StoragePool], Volume]:
    '''Provide a function that defines volumes given a storage pool, name, and size.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool, size: int = 1024 * 1024) -> Volume:
        return pool.define_volume(volume_xml(pool, size))

    return inner


@pytest.fixture
def test_volume(
    test_pool: tuple[StoragePool, Hypervisor],
    volume_factory: Callable[[StoragePool], Volume],
) -> Generator[tuple[Volume, StoragePool, Hypervisor], None, None]:
    '''Provide a Volume instance to operate on.

       Yields a tuple of the Volume instance, the parent StoragePool,
       and the associated Hypervisor.'''
    pool, hv = test_pool
    vol = volume_factory(pool)
    key = vol.key

    yield (vol, pool, hv)

    if pool.volumes.get(key) is not None:
        vol.undefine()


@pytest.fixture
def live_volume(
    live_pool: tuple[StoragePool, Hypervisor],
    volume_factory: Callable[[StoragePool], Volume],
) -> Generator[tuple[Volume, StoragePool, Hypervisor], None, None]:
    '''Provide a Volume instance to operate on.

       Yields a tuple of the Volume instance, the parent StoragePool,
       and the associated Hypervisor.'''
    pool, hv = live_pool
    vol = volume_factory(pool)
    key = vol.key

    yield (vol, pool, hv)

    if pool.volumes.get(key) is not None:
        vol.undefine()
