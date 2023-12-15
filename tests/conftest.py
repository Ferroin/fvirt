# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Test fixtures for fvirt'''

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys

from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from pathlib import Path
from textwrap import dedent
from traceback import format_exception
from typing import TYPE_CHECKING, Any, cast

import pytest

from lxml import etree
from ruamel.yaml import YAML
from simple_file_lock import FileLock

from fvirt.cli import cli
from fvirt.libvirt import URI, Domain, Hypervisor, StoragePool, Volume
from fvirt.libvirt.events import start_libvirt_event_thread

if TYPE_CHECKING:
    from collections.abc import Sequence

    from click.testing import CliRunner, Result

if not sys.warnoptions:
    import warnings

    warnings.filterwarnings('default', category=DeprecationWarning, module='^fvirt')
    warnings.filterwarnings('default', category=SyntaxWarning)
    warnings.filterwarnings('default', category=RuntimeWarning)
    warnings.filterwarnings('default', category=PendingDeprecationWarning, module='^fvirt')
    os.environ['PYTHONWARNINGS'] = \
        'default::DeprecationWarning:fvirt,default::SyntaxWarning,default::RuntimeWarning,default::PendingDeprecationWarning:fvirt'


FAIL_NON_RUNNABLE = os.environ.get('FVIRT_FAIL_NON_RUNNABLE_TESTS', 0)
TEST_SKIP = os.environ.get('FVIRT_TEST_SKIP_TESTS', 0)
GROUP_COUNT = int(os.environ.get('FVIRT_TEST_OBJECT_GROUP_SIZE', 3))
NO_KVM = os.environ.get('FVIRT_NO_KVM_FOR_TESTS', 0)

TESTS_PATH = Path(__file__).parent

PREFIX = 'fvirt-test'
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
yaml = YAML()


def skip_or_fail(msg: str) -> None:
    '''Skip or fail a test with the given message.'''
    if FAIL_NON_RUNNABLE:
        pytest.fail(msg)
    else:
        pytest.skip(msg)


def remove_domain(dom: Domain) -> None:
    '''Remove a domain cleanly.'''
    if dom.running:
        dom.destroy()

    dom.undefine()


def remove_pool(pool: StoragePool) -> None:
    '''Remove a storage pool cleanly.'''
    if pool.running:
        for vol in pool.volumes:
            vol.delete()

        pool.destroy()

    try:
        pool.delete()
    except Exception:
        pass

    pool.undefine()


def cleanup_hv(hv: Hypervisor, prefix: str) -> None:
    '''Clean up any objects created by our tests on the given hypervisor.'''
    for dom in hv.domains:
        if dom.name.startswith(prefix):
            remove_domain(dom)

    for pool in hv.storage_pools:
        if pool.name.startswith(prefix):
            remove_pool(pool)


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
def object_name_prefix(worker_id: str) -> str:
    '''Provide the object name prefix for fvirt tests.'''
    return f'{PREFIX}-{worker_id}-'


@pytest.fixture(scope='session')
def name_factory(unique: Callable[..., str], object_name_prefix: str) -> Callable[[], str]:
    '''Provide a factory function for creating names for objects.'''
    def inner() -> str:
        return unique('text', prefix=object_name_prefix.rstrip('-'))

    return inner


@pytest.fixture(scope='session')
def libvirt_event_loop() -> None:
    '''Ensure that fvirt's libvirt event loop is running.'''
    start_libvirt_event_thread()
    return None


@pytest.fixture(scope='session')
def lock_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    '''Provide a session-scoped lock directory.'''
    return tmp_path_factory.getbasetemp() / 'lock'


@pytest.fixture(scope='session')
def serial(lock_dir: Path) -> Callable[[str], _GeneratorContextManager[None]]:
    '''Provide a callable to serialize parts of a test against other tests.'''
    @contextmanager
    def inner(path: str) -> Generator[None, None, None]:
        with FileLock(lock_dir / path):
            yield

    return inner


@pytest.fixture(scope='session')
def virtqemud() -> str | None:
    '''Provide a path to virtqemud.'''
    virtqemud = shutil.which('virtqemud')

    if virtqemud is None:
        virtqemud = shutil.which('libvirtd')

    return virtqemud


@pytest.fixture(scope='session')
def sys_arch() -> str | None:
    '''Provide the system CPU architecture.'''
    arch: str | None = platform.machine()

    match arch:
        case 'AMD64':
            arch = 'x86_64'
        case 'ARM64':
            arch = 'aarch64'
        case '':
            arch = None

    return arch


@pytest.fixture(scope='session')
def qemu_system(sys_arch: str) -> tuple[Path, str] | None:
    '''Provide a path to a native qemu-system emulator.'''
    arches = (
        'x86_64',
        'aarch64',
    )

    qemu = None

    for arch in (sys_arch,) + arches:
        qemu = shutil.which(f'qemu-system-{arch}')

        if qemu is not None:
            return (Path(qemu), arch)

    return None


@pytest.fixture
def virt_xml_validate(tmp_path: Path) -> Callable[[str], None]:
    '''Provide a function that will validate a libvirt XML document.

       This uses the virt-xml-validate command from the host. If
       this command is not found, it will skip or fail the test
       automatically.

       The schema to use will be inferred automatically from the name
       of the root tag of the document that gets passed in.'''
    if TEST_SKIP:
        skip_or_fail('Requested skipping possibly skipped tests.')

    cmd = shutil.which('virt-xml-validate')

    if cmd is None:
        skip_or_fail('Could not find virt-xml-validate, which is required to run this test.')

    def inner(doc: str) -> None:
        assert cmd is not None

        path = tmp_path / 'test.xml'
        path.write_text(doc)

        try:
            xml = etree.XML(doc)
        except Exception as err:
            assert False, f'{"".join(format_exception(err))}\n\n{doc}'

        e = xml.find('.')
        assert e is not None
        schema = e.tag

        match schema:
            case 'pool':
                schema = 'storagepool'
            case 'volume':
                schema = 'storagevol'

        result = subprocess.run((cmd, str(path), schema), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert result.returncode == 0, f'{doc}\n\n{result.stdout}'

    return inner


@pytest.fixture
def require_virtqemud(virtqemud: str | None) -> None:
    '''Check for a usable copy of virtqemud and skip or fail if one is not found.'''
    if TEST_SKIP:
        skip_or_fail('Requested skipping possibly skipped tests.')

    if virtqemud is None:
        skip_or_fail('Could not find virtqemud or libvirtd, which is required to run this test.')


@pytest.fixture
def require_qemu(require_virtqemud: None, qemu_system: tuple[Path, str] | None) -> None:
    '''Check for a usable copy of virtqemud and qmeu-system emulator, and skip or fail if one is not found.'''
    if TEST_SKIP:
        skip_or_fail('Requested skipping possibly skipped tests.')

    if qemu_system is None:
        skip_or_fail('Could not find QEMU system emulator, which is required to run this test.')


@pytest.fixture(scope='session')
def vm_kernel(qemu_system: tuple[Path, str]) -> tuple[Path, Path]:
    '''Provides a path to a usable kernel image for booting live VMs.'''
    _, vm_arch = qemu_system
    kernel_image = TESTS_PATH / 'data' / 'images' / vm_arch / 'kernel.img'
    initramfs_image = TESTS_PATH / 'data' / 'images' / vm_arch / 'initramfs.img'

    return (kernel_image, initramfs_image)


@pytest.fixture(scope='session')
def test_uri() -> str:
    '''Provide a libvirt URI to use for testing.'''
    return 'test:///default'


@pytest.fixture
def live_uri(require_virtqemud: None) -> str:
    '''Provide a live libvirt URI to use for testing.'''
    return 'qemu:///session'


@pytest.fixture
def test_hv(test_uri: str) -> Generator[Hypervisor, None, None]:
    '''Provide a fvirt.libvirt.Hypervisor instance for testing.

       The provided instance will utilize the libvirt test driver with
       the default configuration, making it suitble for cases where
       interaction with live resources is not required.

       Because of how the test driver works, tests using this fixture
       do not need to worry about other tests accessing the hypervisor
       concurrently with them, but they do need to account for the
       possibility that the state exposed is not a clean instance of
       the test driver.'''
    hv = Hypervisor(hvuri=URI.from_string(test_uri))

    yield hv


@pytest.fixture
def live_hv(live_uri: str, libvirt_event_loop: None, object_name_prefix: str, require_virtqemud: None) -> Generator[Hypervisor, None, None]:
    '''Provide a fvirt.libvirt.Hypervisor instance for testing.

       The provided instance will utilize the libvirt QEMU driver in
       session mode, making it suitable for cases that cannot be tested
       with the test driver, such as storage volume handling or live
       domain operations.

       This fixture may spawn an instance of libvirtd or virtqemud for
       the user running the tests if there is not one already running.

       Because this connects to a shared instance of libvirtd, test cases
       and fixtures that use this fixture should be written in such a
       way that they are safe against concurrent access and usage of
       the hypervisor, and should also make no assumptions about the
       initial state of the hypervisor.'''
    hv = Hypervisor(hvuri=URI.from_string(live_uri))

    yield hv

    cleanup_hv(hv, object_name_prefix)


@pytest.fixture
def test_dom_xml(unique: Callable[..., Any], name_factory: Callable[[], str]) -> Callable[[], str]:
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
def test_dom_template(
    unique: Callable[..., Any],
    tmp_path: Path,
) -> Callable[[str, str], Path]:
    '''Provide a factory that produces domain template files.'''
    def inner(name: str, tmpl_type: str) -> Path:
        uuid = unique('uuid')
        filepath = tmp_path / cast(str, unique('digits'))

        tmpl = {
            'type': 'test',
            'name': name,
            'uuid': str(uuid),
            'memory': 1024 * 1024 * 64,
            'vcpu': 2,
            'os': {
                'variant': 'test',
                'type': 'hvm',
                'arch': 'x86_64',
            },
            'clock': {
                'offset': 'utc',
            },
            'devices': {
                'disks': [
                    {
                        'type': 'file',
                        'src': '/guest/diskimage1',
                        'target': {
                            'dev': 'vda',
                        },
                        'boot': 1,
                    },
                ],
                'net': [
                    {
                        'type': 'network',
                        'src': 'default',
                        'target': 'testnet0',
                        'mac': 'aa:bb:cc:dd:ee:ff',
                    },
                ],
                'memballoon': [
                    {
                        'model': 'virtio',
                    },
                ],
            },
        }

        match tmpl_type:
            case 'json':
                with open(filepath, 'w') as f:
                    json.dump(tmpl, f)
            case 'yaml':
                with open(filepath, 'w') as f:
                    yaml.dump(tmpl, f)

        return filepath

    return inner


@pytest.fixture
def live_dom_xml(
    sys_arch: str,
    live_hv: Hypervisor,
    require_qemu: None,
    qemu_system: tuple[Path, str] | None,
    vm_kernel: tuple[Path, Path],
    unique: Callable[..., Any],
    name_factory: Callable[[], str]
) -> Callable[[], str]:
    '''Provide a factory that produces domain XML strings.'''
    assert qemu_system is not None
    _, vm_arch = qemu_system

    kernel, initramfs = vm_kernel

    match vm_arch:
        case 'x86_64':
            machine = 'q35'
            console = 'ttyS0'

            if live_hv.version is not None and live_hv.version.major < 9:
                panic = 'isa'
            else:
                panic = 'pvpanic'
        case 'aarch64':
            machine = 'virt'
            console = 'ttyAMA0'
            panic = 'pvpanic'
        case _:
            assert False, 'Unsupported VM architecture.'

    if sys_arch == vm_arch and not NO_KVM:
        dom_type = 'kvm'
    else:
        dom_type = 'qemu'

    def inner() -> str:
        name = name_factory()
        uuid = unique('uuid')

        return dedent(f'''<domain type='{dom_type}'>
            <name>{name}</name>
            <uuid>{uuid}</uuid>
            <vcpu>2</vcpu>
            <memory unit='MiB'>96</memory>
            <clock offset='utc' />
            <os>
                <type arch='{vm_arch}' machine='{machine}'>hvm</type>
                <kernel>{kernel}</kernel>
                <initrd>{initramfs}</initrd>
                <cmdline>console={console}</cmdline>
            </os>
            <on_poweroff>destroy</on_poweroff>
            <on_reboot>destroy</on_reboot>
            <on_crash>destroy</on_crash>
            <devices>
                <console type='pty'>
                    <target type='serial' />
                </console>
                <panic model='{panic}' />
            </devices>
        </domain>
        ''').lstrip().rstrip()

    return inner


@pytest.fixture
def live_dom_template(
    sys_arch: str,
    live_hv: Hypervisor,
    require_qemu: None,
    qemu_system: tuple[Path, str] | None,
    vm_kernel: tuple[Path, Path],
    unique: Callable[..., Any],
    tmp_path: Path,
) -> Callable[[str, str], Path]:
    '''Provide a factory that produces domain templates.'''
    assert qemu_system is not None
    _, vm_arch = qemu_system

    kernel, initramfs = vm_kernel

    match vm_arch:
        case 'x86_64':
            machine = 'q35'
            console = 'ttyS0'

            if live_hv.version is not None and live_hv.version.major < 9:
                panic = 'isa'
            else:
                panic = 'pvpanic'
        case 'aarch64':
            machine = 'virt'
            console = 'ttyAMA0'
            panic = 'pvpanic'
        case _:
            assert False, 'Unsupported VM architecture.'

    if sys_arch == vm_arch and not NO_KVM:
        dom_type = 'kvm'
    else:
        dom_type = 'qemu'

    def inner(name: str, tmpl_type: str) -> Path:
        uuid = unique('uuid')
        filepath = tmp_path / cast(str, unique('digits'))

        tmpl = {
            'type': dom_type,
            'name': name,
            'uuid': str(uuid),
            'vcpu': 2,
            'memory': 96 * 1024 * 1024,
            'os': {
                'variant': 'direct',
                'arch': vm_arch,
                'machine': machine,
                'type': 'hvm',
                'kernel': str(kernel),
                'initramfs': str(initramfs),
                'cmdline': f'console={console}',
            },
            'on_poweroff': 'destroy',
            'on_reboot': 'destroy',
            'on_crash': 'destroy',
            'clock': {
                'offset': 'utc',
            },
            'devices': {
                'chardev': [
                    {
                        'target': {
                            'category': 'console',
                            'type': 'serial',
                            'port': 0,
                        },
                        'source': {
                            'type': 'pty',
                        },
                    },
                ],
                'panic': [
                    {
                        'model': panic,
                    },
                ],
            },
        }

        match tmpl_type:
            case 'json':
                with open(filepath, 'w') as f:
                    json.dump(tmpl, f)
            case 'yaml':
                with open(filepath, 'w') as f:
                    yaml.dump(tmpl, f)

        return filepath

    return inner


@pytest.fixture
def test_dom(
    test_hv: Hypervisor,
    test_dom_xml: Callable[[], str],
) -> Generator[tuple[Domain, Hypervisor], None, None]:
    '''Provide a running, persistent Domain instance to operate on.

       Yields the domain instance and the associated Hypervisor instance
       in a tuple..'''
    dom = test_hv.define_domain(test_dom_xml())

    dom.start()

    yield (dom, test_hv)

    if dom.valid and dom in test_hv.domains:
        remove_domain(dom)


@pytest.fixture
def test_dom_group(
    test_hv: Hypervisor,
    test_dom_xml: Callable[[], str],
) -> Generator[tuple[tuple[Domain, ...], Hypervisor], None, None]:
    '''Provide a group of running, persistent Domain instances to operate on.

       Yields the a tuple of the domain instances and the associated
       Hypervisor instance as a tuple.'''
    doms = tuple(
        test_hv.define_domain(test_dom_xml()) for _ in range(0, GROUP_COUNT)
    )

    for dom in doms:
        dom.start()

    yield (doms, test_hv)

    for dom in doms:
        if dom.valid and dom in test_hv.domains:
            remove_domain(dom)


@pytest.fixture
def live_dom(
    live_hv: Hypervisor,
    live_dom_xml: Callable[[], str],
    require_qemu: None,
    serial: Callable[[str], _GeneratorContextManager],
) -> Generator[tuple[Domain, Hypervisor], None, None]:
    '''Provide a live domain with a guest OS for testing.

       Unlike the test_dom fixture, this one does _not_ start the domaain.'''
    with serial('live-dom'):
        dom = live_hv.define_domain(live_dom_xml())

    yield (dom, live_hv)

    with serial('live-dom'):
        if dom.valid and dom in live_hv.domains:
            remove_domain(dom)


@pytest.fixture
def live_dom_group(
    live_hv: Hypervisor,
    live_dom_xml: Callable[[], str],
    require_qemu: None,
    serial: Callable[[str], _GeneratorContextManager],
) -> Generator[tuple[tuple[Domain, ...], Hypervisor], None, None]:
    '''Provide a group of live domains with a guest OS for testing.

       Unlike the test_dom fixture, this one does _not_ start the domaain.'''
    with serial('live-dom'):
        doms = tuple(
            live_hv.define_domain(live_dom_xml()) for _ in range(0, GROUP_COUNT)
        )

    yield (doms, live_hv)

    with serial('live-dom'):
        for dom in doms:
            if dom.valid and dom in live_hv.domains:
                remove_domain(dom)


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
def pool_template(unique: Callable[..., Any], tmp_path: Path) -> Callable[[str, str], Path]:
    '''Provide a factory function that produces storage pool templates.'''
    def inner(name: str, tmpl_type: str) -> Path:
        uuid = unique('uuid')
        path = tmp_path / name
        filepath = tmp_path / cast(str, unique('text', suffix=tmpl_type))

        tmpl = {
            'name': name,
            'uuid': str(uuid),
            'type': 'dir',
            'target': {
                'path': str(path),
            },
        }

        match tmpl_type:
            case 'json':
                with open(filepath, 'w') as f:
                    json.dump(tmpl, f)
            case 'yaml':
                with open(filepath, 'w') as f:
                    yaml.dump(tmpl, f)

        return filepath

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
            remove_pool(pool)


@pytest.fixture
def live_pool_group(
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    serial: Callable[[str], _GeneratorContextManager[None]],
) -> Generator[tuple[tuple[StoragePool, ...], Hypervisor], None, None]:
    '''Provide a tuple of storage pools to operate on.

       Yields a tuple of the tuple of StoragePool instances and the
       Hypervisor instance.'''
    with serial('live-pool'):
        pools = tuple(
            live_hv.define_storage_pool(pool_xml()) for _ in range(0, GROUP_COUNT)
        )

    for pool in pools:
        pool.build()
        pool.start()

    yield (pools, live_hv)

    with serial('live-pool'):
        for pool in pools:
            if pool in live_hv.storage_pools:
                remove_pool(pool)


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
            remove_pool(pool)


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
def volume_template(
    name_factory: Callable[[], str],
    tmp_path: Path,
    unique: Callable[..., str],
) -> Callable[[StoragePool, str, int], Path]:
    '''Provide a function that, given a storage pool and size, will produce a template for a volume.

       The storage pool used should be a directory type pool.'''
    def inner(pool: StoragePool, tmpl_type: str, size: int = 1024 * 1024) -> Path:
        name = name_factory()
        filepath = tmp_path / unique('text', suffix=tmpl_type)

        tmpl = {
            'name': name,
            'type': 'file',
            'capacity': size,
            'allocated': 0,
            'format': 'raw',
            'pool_type': 'dir',
        }

        match tmpl_type:
            case 'json':
                with open(filepath, 'w') as f:
                    json.dump(tmpl, f)
            case 'yaml':
                with open(filepath, 'w') as f:
                    yaml.dump(tmpl, f)

        return filepath

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


@pytest.fixture
def live_volume_group(
    live_pool: tuple[StoragePool, Hypervisor],
    volume_factory: Callable[[StoragePool], Volume],
) -> Generator[tuple[tuple[Volume, ...], StoragePool, Hypervisor], None, None]:
    '''Provide a group of Volume instances to operate on.

       Yields a tuple of a tuple of the Volume instances, the parent StoragePool,
       and the associated Hypervisor.'''
    pool, hv = live_pool

    vols = tuple(
        volume_factory(pool) for _ in range(0, GROUP_COUNT)
    )

    yield (vols, pool, hv)

    for vol in vols:
        if vol in pool.volumes:
            vol.undefine()
