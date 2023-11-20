# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Pydantic models for domain templating.

   These are usable for stricter type checking and validation for the
   Domain.new_config class method.

   Note that even when using these models, the validation performed
   is far from exhaustive, and it is still entirely possible for
   Domain.new_config() to produce a domain configuration that is not
   actually accpeted by libvirt.'''

from __future__ import annotations

import re

from collections.abc import Mapping, Sequence
from typing import Literal, Self
from uuid import UUID

from psutil import cpu_count
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

IPV4_PATTERN = re.compile(
    r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
)

IPV6_PATTERN = re.compile(
    r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
)

YES_NO = Literal['yes', 'no']
ON_OFF = Literal['on', 'off']
CHARDEV_SRC_TYPE = Literal['stdio', 'file', 'vc', 'null', 'pty', 'dev', 'pipe', 'tcp', 'unix', 'spiceport', 'nmdm']


def is_valid_ipv4(ip: str) -> bool:
    match = IPV4_PATTERN.match(ip)
    if match:
        octets = [int(match.group(i)) for i in range(1, 5)]

        if all(0 <= octet <= 255 for octet in octets):
            return True

    return False


def is_valid_ipv6(ip: str) -> bool:
    return bool(IPV6_PATTERN.match(ip))


class PCIAddress(BaseModel):
    '''Model representing a PCI address.'''
    bus: str = Field(pattern='^0x[0-9a-f]{2}$')
    slot: str = Field(pattern='^0x[0-9a-f]{2}$')
    function: str = Field(default='0x0', pattern='^0x[0-9a-f]$')
    domain: str | None = Field(default=None, pattern='^0x[0-9a-f]{4}$')
    multifunction: str | None = Field(default=None, pattern='^(on|off)$')


class DriveAddress(BaseModel):
    '''Model representing a 'drive' address.'''
    controller: int | None = Field(default=None, ge=0)
    bus: int = Field(default=0, ge=0)
    target: int = Field(default=0, ge=0)
    unit: int = Field(default=0, ge=0)


class DataRate(BaseModel):
    '''Model representing a data transfer rate.'''
    bytes: int = Field(gt=0)
    period: int | None = Field(default=None, gt=0)


class MemtuneInfo(BaseModel):
    '''Model representing the contents of a <memtune> element in domain XML.

       `hard` is the hard memory limit.

       `soft` is the soft memory limit.

       `swap` is the swap hard limit.

       `min` is the minimum memory guarantee.

       All values are expressed as bytes. A value of None indicates no limit.'''
    hard: int | None = Field(default=None, gt=0)
    soft: int | None = Field(default=None, gt=0)
    swap: int | None = Field(default=None, gt=0)
    min: int | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def check_limits(self: Self) -> Self:
        if not self.model_fields_set:
            raise ValueError('At least one limit must be set. To set no limits, simply don’t include the memtune property.')

        return self


class CPUModelInfo(BaseModel):
    '''Model representing the <model> element of the <cpu> element in domain XML.

       `name` is the name of the CPU model to use.

       `fallback` defines the fallback behavior for the CPU model
       handling. A value of None means to use the default fallback
       behavior.'''
    name: str = Field(min_length=1)
    fallback: str | None = Field(default=None, min_length=1)


class CPUTopology(BaseModel):
    '''Model representing the CPU topology for a domain.

       If `infer` is set to a value of 'threads', the threads property
       will be automatically inferred from system topology if possible
       using psutil.cpu_count(). This is useful for VMs which will have
       their vcpus pinned to specific host CPUs.

       `coalesce` indicates what level of topology the automatic fixup
       based on vcpus should happen at. If the topology does not match the
       number of vcpus, then the properties other than the one specified
       by `coalesce` will be set to 1 and the property specified by
       `coalesce` will be set to the number of vcpus. A value of None
       for `coalesce` will try to minimize how many properties need to
       be reset. If not using pinned vcpus, a value of 'sockets' is
       recommended for `coalesce`.'''
    infer: Literal['threads'] | None = Field(default=None)
    coalesce: Literal['sockets', 'dies', 'cores', 'threads'] | None = Field(default=None)
    sockets: int = Field(default=1, gt=0)
    dies: int = Field(default=1, gt=0)
    cores: int = Field(default=1, gt=0)
    threads: int = Field(default=1, gt=0)

    @model_validator(mode='after')
    def infer_values(self: Self) -> Self:
        if self.infer == 'threads':
            lcpus = cpu_count(logical=True)
            pcpus = cpu_count(logical=False)

            if lcpus is not None and pcpus is not None:
                self.threads = lcpus // pcpus

        return self

    @property
    def total_cpus(self: Self) -> int:
        '''Total number of logical CPUs described by the topology info.'''
        return self.sockets * self.dies * self.cores * self.threads

    def check(self: Self, vcpus: int) -> None:
        '''Propery sync up the topology info with the vcpu count.

           If the topology is valid for the number of vcpus, do nothing.

           Otherwise if `coalesce` is set, set the property it specified
           to the number of vcpus and all other properties to 1.

           Otherwise, try to sync up the topology with the vcpu count
           with minimal changes.

           The exact manner in which this coerces the topology to match
           the vcpu count is considered to be an implementation detail
           and should not be relied on by users.'''
        if vcpus < 1:
            raise ValueError('Number of vcpus should be a positive integer')

        if self.total_cpus == vcpus:
            return

        if self.coalesce is None:
            if self.dies * self.cores * self.threads == vcpus:
                self.sockets = 1
                return

            if self.cores * self.threads == vcpus:
                self.sockets = 1
                self.dies = 1
                return

            self.sockets = 1
            self.dies = 1
            self.cores = vcpus
            self.threads = 1
        else:
            self.sockets = 1
            self.dies = 1
            self.cores = 1
            self.threads = 1

            setattr(self, self.coalesce, vcpus)


class CPUInfo(BaseModel):
    '''Model representing the contents of the <cpu> element in domain XML.

       `mode` indicates the value for the `mode` attribute of the
       element. A value of None means to use the default defined by
       the templates.

       `model` is an optional CPUModelInfo instance desribing the <model>
       element. A value of None means this element will be omitted in
       the config.

       `sockets` indicates the number of CPU sockets to use.

       `dies` indicates the number of dies per CPU socket to use.

       `cores` indicates the number of CPU cores per die to use.

       `threads` indicates the number of threads per CPU core to use.'''
    mode: str | None = Field(default=None, min_length=1)
    model: CPUModelInfo | None = Field(default=None)
    topology: CPUTopology = Field(default_factory=CPUTopology)


class OSFWLoaderInfo(BaseModel):
    '''Model representing the contents of a <loader> element in an <os> element when in firmware mode.

       `path` specifies the path to the loader file. A value of None
       requests for the hypervisor to autoselect firmware.

       The remaining attributes specifiy values for the corresponding
       attributes on the <loader> element. A value of None '''
    path: str | None = Field(default=None, min_length=1)
    readonly: YES_NO | None = Field(default=None)
    secure: YES_NO | None = Field(default=None)
    stateless: YES_NO | None = Field(default=None)
    type: str | None = Field(default=None, min_length=1)


class OSFWNVRAMInfo(BaseModel):
    '''Model representing the contents of a <nvram> element in an <os> element when in firmware mode.

       Currently, this only supports templated NVRAM file generation.

       `path` specifies the path to the NVRAM file.

       `template` specifies the template file to use.'''
    path: str = Field(min_length=1)
    template: str = Field(min_length=1)


class OSContainerIDMapEntry(BaseModel):
    '''Model representing an idmap entry for the <os> element in domain configuration.

       `target` and `count` correspond to those attributes on the subelements of the <idmap> element.'''
    target: int = Field(ge=0)
    count: int = Field(gt=0)


class OSContainerIDMapInfo(BaseModel):
    '''Model representing the <idmap> element in the <os> element in domain configuration.

       The `uid` and `gid` properties correspond to those specific
       sub-elements of the <idmap> element.'''
    uid: OSContainerIDMapEntry
    gid: OSContainerIDMapEntry


class OSInfo(BaseModel):
    '''Model representing the <os> element in domain configuration.

       `firmware` corresponds to the attribute of the same name on the
       <os> element.

       `variant` identifies the specific type of OS configuration to
       use. It is not directly represented on template output, but
       dictates what structure to use when templating.

       A value of `firmware` for `variant` indicates a conventional
       bootloader setup. The `loader` property must be a OSFWLoaderInfo
       instance if present, and only it and the `nvram` property are
       honored.

       A value of `host` for `variant` indicates use of a host-side
       bootloader, such as Xen’s pygrub or Bhyve’s bhyveload. The
       `bootloader` property must be a string pointing to a usable command
       for this purpose, and the optional `bootloader_args` property
       specifies any extra arguments to pass to that command. Only those
       two properties are honored.

       A value of 'direct` for `variant` indicates use of direct kernel
       boot. The `loader`, `kernel`, `initrd`, `cmdline`, and `dtb`
       properties directly correspond to the values for those elements
       under the <os> element in this case, and the `kernel` property
       is required.

       A value of `container` for `variant` indicates a container boot
       setup. The `init` property specifies the executable to use for
       initialization. The `initargs` property is an optional sequence
       of additional arguments to pass to the `init` executable. The
       `initenv` property is an optional mapping indicating environment
       variables to use with the `init` program. The optional `initdir`,
       `inituser`, and `initgroup` propertyies specify the working
       directory, user, and group IDs to use when running the `init`
       program. The optional `idmap` property indicates ID mapping
       behavior to use.

       A value of `test` for `variant` indicates the minimal OS setup
       used for domains defined for the libvirt test driver.

       The optional `arch` property specifies the CPU architecture for
       the domain. A value of None indicates that this is unspecified.

       The optional `machine` property specifies the emulated machine
       model for the domain. A value of None indicates that this is
       unspecified.

       The optional `type` property specifies the type of domain, such
       as hvm or pv. A value of None indicates to use a sensible default
       for this.'''
    variant: str = Field(pattern='^(firmware|host|direct|container|test)$')
    firmware: str | None = Field(default=None, min_length=1)
    arch: str | None = Field(default=None, min_length=1)
    machine: str | None = Field(default=None, min_length=1)
    type: str | None = Field(default=None, min_length=1)
    loader: OSFWLoaderInfo | str | None = Field(default=None)
    nvram: OSFWNVRAMInfo | None = Field(default=None)
    bootloader: str | None = Field(default=None, min_length=1)
    bootloader_args: str | None = Field(default=None)
    kernel: str | None = Field(default=None, min_length=1)
    initrd: str | None = Field(default=None, min_length=1)
    cmdline: str | None = Field(default=None, min_length=1)
    dtb: str | None = Field(default=None, min_length=1)
    init: str | None = Field(default=None, min_length=1)
    initargs: Sequence[str] = Field(default_factory=list)
    initenv: Mapping[str, str] = Field(default_factory=dict)
    initdir: str | None = Field(default=None, min_length=1)
    inituser: str | None = Field(default=None, min_length=1)
    initgroup: str | None = Field(default=None, min_length=1)
    idmap: OSContainerIDMapInfo | None = Field(default=None)

    @model_validator(mode='after')
    def check_variant(self: Self) -> Self:
        match self.variant:
            case 'firmware':
                if isinstance(self.loader, str):
                    raise ValueError('Loader must be an OSFWLoaderInfo instance for variant "firmware".')

                if self.nvram is not None and self.loader is None:
                    raise ValueError('NVRAM may only be specified if loader is also specified.')

                invalid_props = {
                    'bootloader',
                    'bootloader_args',
                    'kernel',
                    'initrd',
                    'cmdline',
                    'dtb',
                    'init',
                    'initargs',
                    'initenv',
                    'initdir',
                    'inituser',
                    'initgroup',
                    'idmap',
                }
            case 'host':
                invalid_props = {
                    'loader',
                    'nvram',
                    'kernel',
                    'initrd',
                    'cmdline',
                    'dtb',
                    'init',
                    'initargs',
                    'initenv',
                    'initdir',
                    'inituser',
                    'initgroup',
                    'idmap',
                }
            case 'direct':
                if isinstance(self.loader, OSFWLoaderInfo):
                    raise ValueError('Loader must be a string for variant "direct".')

                invalid_props = {
                    'nvram',
                    'bootloader',
                    'bootloader_args',
                    'init',
                    'initargs',
                    'initenv',
                    'initdir',
                    'inituser',
                    'initgroup',
                    'idmap',
                }
            case 'container':
                if self.init is None or not self.init:
                    raise ValueError('"init" properrty must be defined for variant "container".')

                invalid_props = {
                    'loader',
                    'nvram',
                    'bootloader',
                    'bootloader_args',
                    'kernel',
                    'initrd',
                    'cmdline',
                    'dtb',
                }
            case 'test':
                if self.arch is None:
                    raise ValueError('"arch" property must be defined for variant "test".')

                invalid_props = {
                    'loader',
                    'nvram',
                    'bootloader',
                    'bootloader_args',
                    'kernel',
                    'initrd',
                    'cmdline',
                    'dtb',
                    'init',
                    'initargs',
                    'initenv',
                    'initdir',
                    'inituser',
                    'initgroup',
                    'idmap',
                }
            case _:
                raise RuntimeError

        for item in invalid_props:
            if getattr(self, item):
                raise ValueError(f'"{ item }" property is not valid for variant "{ self.variant }".')

        return self


class ClockTimerInfo(BaseModel):
    '''Model representing a timer configuration within the clock configurationf or a domain.

       All properties correspond directly to the attributes of the same
       name for the resultant <timer /> element.'''
    name: str
    track: str | None = Field(default=None, min_length=1)
    tickpolicy: str | None = Field(default=None, min_length=1)
    present: YES_NO | None = Field(default=None)


class ClockInfo(BaseModel):
    '''Model representing clock configuration for a domain.

       Other than the `timers` property, all properties correspond
       directly to the properties of the same name on the <clock>
       element in the domain config.

       The `timers` property is a sequence of ClockTimerInfo instances
       to add to the clock element.'''
    offset: Literal['utc', 'localtime', 'timezone', 'variable', 'absolute'] = Field(default='utc')
    tz: str | None = Field(default=None, min_length=1)
    basis: Literal['utc', 'localtime'] | None = Field(default=None)
    adjustment: str | None = Field(default=None, min_length=1)
    start: int | None = Field(default=None)
    timers: Sequence[ClockTimerInfo] = Field(default_factory=list)


class FeaturesHyperVSpinlocks(BaseModel):
    '''Model representing Hyper-V spinlock config for domain features.

       The `state` and `retries` properties correspond to the attributes
       of the same name on the <spinlocks /> element.'''
    state: ON_OFF
    retries: int | None = Field(default=None, gt=4095)


class FeaturesHyperVSTimer(BaseModel):
    '''Model representing Hyper-V stimer config for domain features.

       The `state` and `direct` properties correspond to the attributes
       of the same name on the <stime /> element.'''
    state: ON_OFF
    direct: ON_OFF | None = Field(default=None)


class FeaturesHyperVVendorID(BaseModel):
    '''Model representing Hyper-V vendor_id config for domain features.

       The `state` and `value` properties correspond to the attributes
       of the same name on the <vendor_id /> element.'''
    state: ON_OFF
    value: str | None = Field(default=None, min_length=1, max_length=12)


class FeaturesHyperVInfo(BaseModel):
    '''Model representing Hyper-V features configuration for a domain.

       `mode` corresponds to the attribute of the same name for the
       <hyperv> element. Users should not need to set it manually,
       as the correct value will be automatically inferred based on
       whether any other properties are set or not.

       Other properties correspond to the elements of the same name
       that would be put in the <hyperv> element in the config.'''
    mode: Literal['passthrough', 'custom'] = Field(default='passthrough')
    avic: ON_OFF | None = Field(default=None)
    evmcs: ON_OFF | None = Field(default=None)
    frequencies: ON_OFF | None = Field(default=None)
    ipi: ON_OFF | None = Field(default=None)
    reenlightenment: ON_OFF | None = Field(default=None)
    relaxed: ON_OFF | None = Field(default=None)
    reset: ON_OFF | None = Field(default=None)
    runtime: ON_OFF | None = Field(default=None)
    spinlocks: FeaturesHyperVSpinlocks | None = Field(default=None)
    stimer: FeaturesHyperVSTimer | None = Field(default=None)
    synic: ON_OFF | None = Field(default=None)
    tlbflush: ON_OFF | None = Field(default=None)
    vapic: ON_OFF | None = Field(default=None)
    vendor_id: FeaturesHyperVVendorID | None = Field(default=None)
    vpindex: ON_OFF | None = Field(default=None)

    @model_validator(mode='after')
    def fixup_mode(self: Self) -> Self:
        for item in self.model_fields_set:
            if item != 'mode' and getattr(self, item) is not None:
                self.mode = 'custom'
                break

        return self


class FeaturesKVMDirtyRing(BaseModel):
    '''Model representing KVM dirty-ring config for domain features.

       The properties correspond to the equivalently named attributes
       on the <dirty-ring /> element.'''
    state: ON_OFF
    size: int | None = Field(default=None, ge=1024, le=65536)

    @field_validator('size')
    @classmethod
    def check_size(cls: type[FeaturesKVMDirtyRing], v: int | None, info: ValidationInfo) -> int | None:
        if v is not None and v > 0 and (v & (v - 1)) != 0:
            raise ValueError('"size" property must be a power of 2 between 1024 and 65536')

        return v


class FeaturesKVMInfo(BaseModel):
    '''Model representing KVM features configuration for a domain.

       The properties correspond to the equivalently named elements that
       can be found in the <kvm> element in the domain configuration.'''
    dirty_ring: FeaturesKVMDirtyRing | None = Field(default=None)
    hidden: ON_OFF | None = Field(default=None)
    hint_dedicated: ON_OFF | None = Field(default=None)
    poll_control: ON_OFF | None = Field(default=None)
    pv_ipi: ON_OFF | None = Field(default=None)


class FeaturesXenPassthrough(BaseModel):
    '''Model representing Xen passthrough config for domain features.

       The properties correspond to the equivalently named attributes
       on the <passthrough /> element.'''
    state: ON_OFF
    mode: Literal['sync_pt', 'share_pt'] | None = Field(default=None)


class FeaturesXenInfo(BaseModel):
    '''Model representing Xen features configuration for a domain.

       The properties correspond to the equivalently named elements that
       can be found in the <xen> element in the domain configuration.'''
    e820_host: ON_OFF | None = Field(default=None)
    passthrough: FeaturesXenPassthrough | None = Field(default=None)


class FeaturesTCGInfo(BaseModel):
    '''Model representing TCG features configuration for a domain.

       The `tb_cache` property indicates the size in mibibytes (not
       bytes or megabytes) of the TCG translation block cache.'''
    tb_cache: int | None = Field(default=None, gt=0)


class FeaturesAPICInfo(BaseModel):
    '''Model representing APIC features configuration for a domain.

       The `eoi` property corresponds to the attribute of the same name
       on the <apic /> element in the domain configuration. A value of
       None for that property indicates that an <apic /> element should
       be present, but should not have any attributes.'''
    eoi: ON_OFF | None = Field(default=None)


class FeaturesGICInfo(BaseModel):
    '''Model representing GIC features configuration for a domain.

       The `version` property corresponds to the attribute of the same
       name on the <gic /> element in the domain configuration. A value
       of None for that property indicates that an <gic /> element should
       be present, but should not have any attributes.'''
    version: Literal['2', '3', 'host'] | None = Field(default=None)


class FeaturesIOAPICInfo(BaseModel):
    '''Model representing IOAPIC features configuration for a domain.

       The `driver` property corresponds to the attribute of the same
       name on the <ioapic /> element in the domain configuration. A
       value of None for that property indicates that an <ioapic />
       element should be present, but should not have any attributes.'''
    driver: Literal['kvm', 'qemu'] | None = Field(default=None)


class FeaturesCapabilities(BaseModel):
    '''Model representing capabilities configuration for a domain.

       The `policy` property corresponds to the attribute of the same
       name on the <capabilities> element in the domain configuration.

       The `modify` property is a mapping of capability names to
       capability states, with each entry corresponding to an element
       under the <capabilities> element.'''
    policy: Literal['default', 'allow', 'deny']
    modify: Mapping[str, str] = Field(default_factory=dict)

    @field_validator('modify')
    @classmethod
    def check_modify(cls: type[FeaturesCapabilities], m: Mapping[str, str], info: ValidationInfo) -> Mapping[str, str]:
        for k, v in m.items():
            if v not in {'on', 'off'}:
                raise ValueError(f'Value "{ v }" for key "{ k }" in property "modify" is not valid, must be "on" or "off"')

        return m


class FeaturesInfo(BaseModel):
    '''Model representing the contents of the <features> element in domain configuration.

       The individual properties correspond to the elements of the
       equivalent name found in the <features> element in the domain
       configuration.'''
    acpi: bool | None = Field(default=None)
    apic: FeaturesAPICInfo | None = Field(default=None)
    async_teardown: ON_OFF | None = Field(default=None)
    caps: FeaturesCapabilities | None = Field(default=None)
    gic: FeaturesGICInfo | None = Field(default=None)
    hap: ON_OFF | None = Field(default=None)
    htm: ON_OFF | None = Field(default=None)
    hyperv: FeaturesHyperVInfo | None = Field(default=None)
    kvm: FeaturesKVMInfo | None = Field(default=None)
    pae: bool | None = Field(default=None)
    pmu: ON_OFF | None = Field(default=None)
    pvspinlock: ON_OFF | None = Field(default=None)
    smm: ON_OFF | None = Field(default=None)
    tcg: FeaturesTCGInfo | None = Field(default=None)
    vmcoreinfo: ON_OFF | None = Field(default=None)
    vmport: ON_OFF | None = Field(default=None)
    xen: FeaturesXenInfo | None = Field(default=None)


class ControllerDriverInfo(BaseModel):
    '''Model representing a driver element in a controller device entry.'''
    queues: int | None = Field(default=None, gt=0)
    cmd_per_lun: int | None = Field(default=None, gt=0)
    max_sectors: int | None = Field(default=None, gt=0)


class ControllerDevice(BaseModel):
    '''Model representing a controller device in domain configuration.'''
    type: str = Field(min_length=1)
    index: int | None = Field(default=None, ge=0)
    driver: ControllerDriverInfo | None = Field(default=None)
    maxEventChannels: int | None = Field(default=None, gt=0)
    maxGrantFrames: int | None = Field(default=None, gt=0)
    model: str | None = Field(default=None, min_length=1)
    ports: int | None = Field(default=None, gt=0)
    vectors: int | None = Field(default=None, gt=0)


class DiskVolumeSrcInfo(BaseModel):
    '''Model representing a disk device volume source.'''
    pool: str = Field(min_length=1)
    volume: str = Field(min_length=1)


class DiskTargetInfo(BaseModel):
    '''Model representing a disk device target.'''
    dev: str = Field(min_length=1)
    addr: PCIAddress | DriveAddress | None = Field(default=None)
    bus: str | None = Field(default=None, min_length=1)
    removable: ON_OFF | None = Field(default=None)
    rotation_rate: int | None = Field(default=None, gt=0, lt=65535)

    @model_validator(mode='after')
    def check_addr(self: Self) -> Self:
        if self.addr is not None:
            if self.bus is None:
                raise ValueError('Disk target address may only be specified if a target bus is specified.')

            joiner = '" or "'

            match self.addr:
                case PCIAddress():
                    valid_bus = {'virtio', 'xen'}

                    if self.bus not in valid_bus:
                        raise ValueError(f'PCI addresses for disk targets are only supported for a bus of "{joiner.join(valid_bus)}".')
                case DriveAddress():
                    valid_bus = {'scsi', 'ide', 'usb', 'sata', 'sd'}

                    if self.bus not in valid_bus:
                        raise ValueError(f'Drive addresses for disk targets are only supported for a bus of "{joiner.join(valid_bus)}".')
                case _:
                    raise RuntimeError

        return self


class DiskDevice(BaseModel):
    '''Model representing a disk device in domain config.'''
    type: Literal['file', 'block', 'volume']
    src: str | DiskVolumeSrcInfo
    target: DiskTargetInfo
    boot: int | None = Field(default=None, gt=0)
    device: Literal['disk', 'floppy', 'cdrom', 'lun'] | None = Field(default=None)
    readonly: bool = Field(default=False)
    snapshot: Literal['internal', 'external', 'manual', 'no'] | None = Field(default=None)
    startup: Literal['mandatory', 'requisite', 'optional'] | None = Field(default=None)

    @model_validator(mode='after')
    def check_startup(self: Self) -> Self:
        if self.startup is not None and self.type not in {'file', 'volume'}:
            raise ValueError('Startup property is only supported for "file" or "volume" type disks.')

        return self


class FilesystemDriverInfo(BaseModel):
    '''Model representing a filesystem device driver in domain config.'''
    type: str = Field(min_length=1)
    format: str | None = Field(default=None, min_length=1)
    queues: str | None = Field(default=None, min_length=1)
    wrpolicy: str | None = Field(default=None, min_length=1)


class Filesystem(BaseModel):
    '''Model representing a filesystem device in domain config.'''
    type: Literal['mount', 'template', 'file', 'block', 'ram', 'bind']
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    accessmode: Literal['passthrough', 'mapped', 'squash'] | None = Field(default=None)
    dmode: str | None = Field(default=None, min_length=1)
    driver: FilesystemDriverInfo | None = Field(default=None)
    fmode: str | None = Field(default=None, min_length=1)
    multidev: Literal['default', 'remap', 'forbid', 'warn'] | None = Field(default=None)
    readonly: bool = Field(default=False)
    src_type: str | None = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def set_src_type(self: Self) -> Self:
        if self.src_type is None:
            if self.type == 'ram':
                self.src_type = 'usage'
            elif self.type == 'template':
                self.src_type = 'name'
            elif self.type == 'file':
                self.src_type = 'file'

        return self


class NetworkVPort(BaseModel):
    '''Model representing a virtualport element for a network interface.'''
    instanceid: str | None = Field(default=None, min_length=1)
    interfaceid: str | None = Field(default=None, min_length=1)
    managerid: str | None = Field(default=None, min_length=1)
    profileid: str | None = Field(default=None, min_length=1)
    typeid: str | None = Field(default=None, min_length=1)
    typeidversion: str | None = Field(default=None, min_length=1)


class NetworkIPInfo(BaseModel):
    '''Model representing IP config for a user network driver.'''
    address: str
    prefix: int

    @model_validator(mode='after')
    def check_model(self: Self) -> Self:
        if is_valid_ipv4(self.address):
            if self.prefix not in range(1, 32):
                raise ValueError('Prefix must be an integer between 1 and 31 inclusive for an IPv4 address.')
        elif is_valid_ipv6(self.address):
            if self.prefix not in range(1, 128):
                raise ValueError('Prefix must be an integer between 1 and 127 inclusive for an IPv6 address.')
        else:
            raise ValueError(f'"{ self.address }" does not appear to be a valid IPv4 or IPv6 address.')

        return self


class NetworkInterface(BaseModel):
    '''Model representing a network interface in domain configuration.'''
    type: Literal['network', 'bridge', 'direct', 'user']
    src: str | None = Field(default=None, min_length=1)
    mode: Literal['vepa', 'bridge', 'private', 'passthrough'] | None = Field(default=None)
    target: str | None = Field(default=None, min_length=1)
    mac: str | None = Field(default=None, pattern='^([0-9a-f]{2}:){5}[0-9a-f]{2}$')
    boot: int | None = Field(default=None, gt=0)
    virtualport: NetworkVPort | None = Field(default=None)
    ipv4: NetworkIPInfo | None = Field(default=None)
    ipv6: NetworkIPInfo | None = Field(default=None)


class InputSource(BaseModel):
    '''Model representing an input device source.'''
    dev: str = Field(min_length=1)
    grab: Literal['all'] | None = Field(default=None)
    repeat: ON_OFF | None = Field(default=None)
    grabToggle: str | None = Field(default=None, min_length=1)


class InputDevice(BaseModel):
    '''Model representing an input device in domain configuration.'''
    type: Literal['keyboard', 'mouse', 'tablet', 'passthrough', 'evdev']
    bus: Literal['usb', 'ps2', 'virtio', 'xen'] | None = Field(default=None)
    model: str | None = Field(default=None, min_length=1)
    src: InputSource | None = Field(default=None)

    @model_validator(mode='after')
    def check_src(self: Self) -> Self:
        if self.type in {'passthrough', 'evdev'} and self.src is None:
            raise ValueError(f'Input source must be specified for type "{ self.type }".')

        return self


class GraphicsListener(BaseModel):
    '''Model for listener entries in graphics elements.'''
    type: Literal['address', 'network', 'socket', 'none']
    address: str | None = Field(default=None, min_length=1)
    network: str | None = Field(default=None, min_length=1)
    socket: str | None = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def check_model(self: Self) -> Self:
        match self.type:
            case 'address':
                none_props: tuple[str, ...] = ('network', 'address')

                if self.address is None:
                    raise ValueError('"address" property must be specified for a listener of type "address".')
            case 'network':
                none_props = ('address', 'socket')

                if self.network is None:
                    raise ValueError('"network" property must be specified for a listener of type "network".')
            case 'socket':
                none_props = ('address', 'network')

                if self.socket is None:
                    raise ValueError('"socket" property must be specified for a listener of type "socket".')
            case 'none':
                none_props = ('address', 'network', 'socket')
            case _:
                raise RuntimeError

        for attr in none_props:
            if getattr(self, attr) is not None:
                raise ValueError(f'Property "{ attr }" must be None for a type of "{ self.type }".')

        return self


class GraphicsDevice(BaseModel):
    '''Model representing a graphics output interface in domain configuration.'''
    type: Literal['vnc', 'spice', 'rdb']
    listeners: Sequence[GraphicsListener] = Field(default_factory=list)
    port: int | None = Field(default=None, gt=0, lt=65536)
    tlsPort: int | None = Field(default=None, gt=0, lt=65536)
    autoport: YES_NO | None = Field(default=None)
    socket: str | None = Field(default=None, min_length=1)
    passwd: str | None = Field(default=None, min_length=1)
    passwdValidTo: str | None = Field(default=None, min_length=1)
    keymap: str | None = Field(default=None, min_length=1)
    connected: Literal['keep', 'disconnect', 'fail'] | None = Field(default=None)
    sharePolicy: Literal['allow-exclusive', 'force-shared', 'ignore'] | None = Field(default=None)
    powerControl: str | None = Field(default=None, min_length=1)
    websocket: int | None = Field(default=None, gt=0, lt=65536)
    audio: str | None = Field(default=None, min_length=1)
    defaultMode: Literal['secure', 'insecure', 'any'] | None = Field(default=None)
    channels: Mapping[str, str] = Field(default_factory=dict)
    multiUser: YES_NO | None = Field(default=None)
    replaceUser: YES_NO | None = Field(default=None)


class VideoDevice(BaseModel):
    '''Model representing a GPU device in domain configuration.'''
    type: Literal['vga', 'cirrus', 'vmvga', 'xen', 'vbox', 'virtio', 'gop', 'bochs', 'ramfb', 'none']
    vram: int | None = Field(default=None, ge=1024)
    heads: int | None = Field(default=None, gt=0)
    blob: ON_OFF | None = Field(default=None)

    @model_validator(mode='after')
    def check_vram(self: Self) -> Self:
        if self.vram is not None and (self.vram & (self.vram-1) != 0):
            raise ValueError('VRAM amount must be a power of 2')

        return self


class CharDevSource(BaseModel):
    '''Model representing a character device source.'''
    path: str | None = Field(default=None, min_length=1)
    channel: str | None = Field(default=None, min_length=1)
    mode: str | None = Field(default=None, min_length=1)
    host: str | None = Field(default=None, min_length=1)
    service: int | None = Field(default=None, gt=0, lt=65536)
    tls: YES_NO | None = Field(default=None)


class CharDevTarget(BaseModel):
    '''Model representing a character device target.'''
    type: str = Field(min_length=1)
    port: int | None = Field(default=None, ge=0)
    address: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    state: str | None = Field(default=None, min_length=1)


class CharDevLog(BaseModel):
    '''Model representing log config for a character device.'''
    file: str = Field(min_length=1)
    append: ON_OFF | None = Field(default=None)


class CharacterDevice(BaseModel):
    '''Model representing a character device in domain configuration.'''
    category: Literal['parallel', 'serial', 'console', 'channel']
    type: CHARDEV_SRC_TYPE
    target: CharDevTarget
    src: CharDevSource | None = Field(default=None)
    log: CharDevLog | None = Field(default=None)


class WatchdogDevice(BaseModel):
    '''Model representing a watchdog device in domain configuration.'''
    model: str = Field(min_length=1)
    action: Literal['reset', 'shutdown', 'poweroff', 'pause', 'none', 'dump', 'inject-nmi'] | None = Field(default=None)


class RNGBackend(CharDevSource):
    '''Model representing a backend for an RNG device in domain configuration.'''
    model: Literal['random', 'builtin', 'egd'] = Field(default='builtin')
    type: CHARDEV_SRC_TYPE | None = Field(default=None)


class RNGDevice(BaseModel):
    '''Model representing an RNG device in domain configuration.'''
    model: str = Field(min_length=1)
    rate: DataRate | None = Field(default=None)
    backend: RNGBackend = Field(default_factory=RNGBackend)


class TPMDevice(BaseModel):
    '''Model representing a TPM device in domain configuration.'''
    type: Literal['passthrough', 'emulator']
    model: Literal['tpm-tis', 'tpm-crb', 'tpm-spapr', 'tpm-spapr-proxy'] | None = Field(default=None)
    dev: str | None = Field(default=None, min_length=1)
    encryption: str | None = Field(default=None, min_length=1)
    version: Literal['1.2', '2.0'] | None = Field(default=None)
    persistent_state: YES_NO | None = Field(default=None)
    active_pcr_banks: Sequence[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def check_state(self: Self) -> Self:
        match self.type:
            case 'passthrough':
                if self.dev is None:
                    raise ValueError('Property "dev" must be specified for type "passthrough".')
            case 'emulator':
                pass
            case _:
                raise RuntimeError

        return self


class SimpleDevice(BaseModel):
    '''Model reprsenting simple devices that only support a model attribute.'''
    model: str = Field(min_length=1)


class Devices(BaseModel):
    '''Model representing device configuration for a domain.'''
    controllers: Sequence[ControllerDevice] = Field(default_factory=list)
    disks: Sequence[DiskDevice] = Field(default_factory=list)
    fs: Sequence[Filesystem] = Field(default_factory=list)
    net: Sequence[NetworkInterface] = Field(default_factory=list)
    input: Sequence[InputDevice] = Field(default_factory=list)
    graphics: Sequence[GraphicsDevice] = Field(default_factory=list)
    video: Sequence[VideoDevice] = Field(default_factory=list)
    chardev: Sequence[CharacterDevice] = Field(default_factory=list)
    watchdog: Sequence[WatchdogDevice] = Field(default_factory=list)
    rng: Sequence[RNGDevice] = Field(default_factory=list)
    tpm: Sequence[TPMDevice] = Field(default_factory=list)
    memballoon: Sequence[SimpleDevice] = Field(default_factory=list)
    panic: Sequence[SimpleDevice] = Field(default_factory=list)

    @model_validator(mode='after')
    def check_controller_indices(self: Self) -> Self:
        seen_indices = set()

        for item in self.controllers:
            if item.index is None:
                continue
            elif item.index in seen_indices:
                raise ValueError(f'Duplicate index "{ item.index }" found in controller entries.')
            else:
                seen_indices.add(item.index)

        return self


class DomainInfo(BaseModel):
    '''Model representing domain configuration for templating.

       Memory values should be provided in bytes unless otherwise noted.

       A value of `0` for the `vcpu` property indicates that the count
       should be inferred from topology information in the `cpu` property
       if possible, otherwise a default value should be used.'''
    name: str = Field(min_length=1)
    type: Literal['hvf', 'kvm', 'lxc', 'vz', 'qemu', 'test', 'xen']
    sub_template: str | None = Field(default=None)
    uuid: UUID | None = Field(default=None)
    genid: UUID | None = Field(default=None)
    vcpu: int = Field(default=0, ge=0)
    memory: int = Field(gt=0)
    memtune: MemtuneInfo | None = Field(default=None)
    cpu: CPUInfo | None = Field(default=None)
    os: OSInfo
    clock: ClockInfo = Field(default_factory=ClockInfo)
    features: FeaturesInfo = Field(default_factory=FeaturesInfo)
    devices: Devices = Field(default_factory=Devices)

    @model_validator(mode='after')
    def set_sub_template(self: Self) -> Self:
        self.sub_template = f'domain/{ self.type }.xml'
        return self

    @model_validator(mode='after')
    def fixup_vcpus(self: Self) -> Self:
        if self.cpu is not None:
            if self.vcpu == 0:
                self.vcpu = self.cpu.topology.total_cpus
            else:
                self.cpu.topology.check(self.vcpu)
        elif self.vcpu == 0:
            self.vcpu = 1

        return self
