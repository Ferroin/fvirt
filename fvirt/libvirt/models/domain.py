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

from collections.abc import Mapping, Sequence
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, ValidationInfo, computed_field, field_validator, model_validator
from pydantic_extra_types.mac_address import MacAddress

from ._types import FileMode, FilePath, Hostname, Model, NetPort, NonEmptyString, V_OnOff, V_Timestamp, V_YesNo


class PCIAddress(Model):
    '''Model representing a PCI address.'''
    bus: Annotated[str, Field(pattern='^0x[0-9a-f]{2}$')] | Annotated[int, Field(ge=0x00, le=0xff)] = Field(
        description='The PCI bus used for this PCI address.',
    )
    slot: Annotated[str, Field(pattern='^0x[01][0-9a-f]$')] | Annotated[int, Field(ge=0x00, le=0x1f)] = Field(
        description='The PCI device on the specified bus.',
    )
    function: Annotated[str, Field(pattern='^0x[0-7]$')] | Annotated[int, Field(ge=0x0, le=0x7)] = Field(
        default='0x0',
        description='The function of the specified device.',
    )
    domain: Annotated[str, Field(pattern='^0x[0-9a-f]{4}$')] | Annotated[int, Field(ge=0x0000, le=0xffff)] | None = Field(
        default=None,
        description='The PCI domain used for this PCI address.',
    )
    multifunction: V_OnOff | None = Field(
        default=None,
        description='Whether to enable multifunction support for this device. Requires QEMU.',
    )


class DriveAddress(Model):
    '''Model representing a 'drive' address.'''
    controller: int | None = Field(
        default=None,
        ge=0,
        description='Index of the controller to use for this drive. If not specified, libvirt will infer a correct value.',
    )
    bus: int = Field(
        default=0,
        ge=0,
        description='Bus number for this drive.',
    )
    target: int = Field(
        default=0,
        ge=0,
        description='Target index for this drive.',
    )
    unit: int = Field(
        default=0,
        ge=0,
        description='Unit index for this drive.',
    )


class DataRate(Model):
    '''Model representing a data transfer rate.'''
    bytes: int = Field(
        gt=0,
        description='Number of bytes that can be transferred in the specified period.',
    )
    period: int = Field(
        default=1000,
        gt=0,
        description='The size of the time window for the limit, specified in miliseconds.',
    )


class MemtuneInfo(Model):
    '''Model representing the contents of a <memtune> element in domain XML.

       `hard` is the hard memory limit.

       `soft` is the soft memory limit.

       `swap` is the swap hard limit.

       `min` is the minimum memory guarantee.

       All values are expressed as bytes. A value of None indicates no limit.'''
    hard: int | None = Field(
        default=None,
        gt=0,
        description='Hard limit on host-side domain memory usage in bytes.',
    )
    soft: int | None = Field(
        default=None,
        gt=0,
        description='Soft limit on host-side domain memory usage in bytes.',
    )
    swap: int | None = Field(
        default=None,
        gt=0,
        description='Hard limit on host-side domain memory and swap usage in bytes.',
    )
    min: int | None = Field(
        default=None,
        gt=0,
        description='Minimum amount of host-side memory available to domain, in bytes.',
    )

    @model_validator(mode='after')
    def check_limits(self: Self) -> Self:
        if not self.model_fields_set:
            raise ValueError('At least one limit must be set. To set no limits, simply don’t include the memtune property.')

        return self


class CPUModelInfo(Model):
    '''Model representing the <model> element of the <cpu> element in domain XML.

       `name` is the name of the CPU model to use.

       `fallback` defines the fallback behavior for the CPU model
       handling. A value of None means to use the default fallback
       behavior.'''
    name: NonEmptyString = Field(
        description='Name of the CPU model. Valid values depend on the domain CPU architecture and the domain type.',
    )
    fallback: Literal['allow', 'forbid'] | None = Field(
        default=None,
        description='Specify fallback behavior if the requested CPU model cannot be used.',
    )


class CPUTopology(Model):
    '''Model representing the CPU topology for a domain.'''
    coalesce: Literal['sockets', 'dies', 'cores', 'threads'] | None = Field(
        default=None,
        description='Controls topology fixup behavior. If the topology does not match the number of VCPUs ' +
                    'assigned to the domain, the specified property will be set to the number of VCPUs ' +
                    'assigned to the domain and the other properties will be set to 1. If unspecified or null, ' +
                    'finer-grained properties will be preserved to the greatest etent possible. If not using ' +
                    "pinned VCPUs, a value of 'sockets' is recommended.",
    )
    sockets: int = Field(
        default=1,
        gt=0,
        description='The number of CPU sockets the system should have.',
    )
    dies: int = Field(
        default=1,
        gt=0,
        description='The number of dies per CPU socket.',
    )
    cores: int = Field(
        default=1,
        gt=0,
        description='The number of physical CPU cores per die.',
    )
    threads: int = Field(
        default=1,
        gt=0,
        description='The number of logical CPUs per CPU core.',
    )

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


class CPUInfo(Model):
    '''Model representing the contents of the <cpu> element in domain XML.

       `mode` indicates the value for the `mode` attribute of the
       element. A value of None means to use the default defined by
       the templates.'''
    mode: Literal['custom', 'host-model', 'host-passthrough', 'maximum'] | None = Field(
        default=None,
        description='The CPU emulation handling mode to use. If left unset, a sane default will be used based on the domain type.',
    )
    model: CPUModelInfo | None = Field(
        default=None,
        description='CPU model configuration for the domain.',
    )
    topology: CPUTopology = Field(
        default_factory=CPUTopology,
        description='CPU topology configuration for the domain. If left unset, a sane default will be inferred based on the number ' +
                    'of VCPUs assigned to the domain.',
    )


class OSFWLoaderInfo(Model):
    '''Model representing the contents of a <loader> element in an <os> element when in firmware mode.

       `path` specifies the path to the loader file. A value of None
       requests for the hypervisor to autoselect firmware.

       The remaining attributes specifiy values for the corresponding
       attributes on the <loader> element. A value of None indicates
       that attribute should not be included.'''
    path: FilePath | None = Field(
        default=None,
        description='The path to the firmware file that should be used. If not specified, the hypervisor will autoselect appropriate firmware.',
    )
    readonly: V_YesNo | None = Field(
        default=None,
        description='Whether the firmware image should be read-only or not.',
    )
    secure: V_YesNo | None = Field(
        default=None,
        description='Whether the firmware is secure-boot capable or not.',
    )
    stateless: V_YesNo | None = Field(
        default=None,
        description='Whether stateless mode should be used or not.',
    )
    type: Literal['rom', 'pflash'] | None = Field(
        default=None,
        description='Indicates how the firmware should be exposed to the guest.',
    )


class OSFWNVRAMInfo(Model):
    '''Model representing the contents of a <nvram> element in an <os> element when in firmware mode.

       Currently, this only supports templated NVRAM file generation.'''
    path: FilePath = Field(
        description='The path to use for the NVRAM image.',
    )
    template: FilePath = Field(
        description='The path to the template to use when generating the NVRAM image.'
    )


class OSContainerIDMapEntry(Model):
    '''Model representing an idmap entry for the <os> element in domain configuration.

       `target` and `count` correspond to those attributes on the subelements of the <idmap> element.'''
    target: int = Field(
        ge=0,
        description='Specifies the first target ID to use for ID mapping.',
    )
    count: int = Field(
        gt=0,
        description='Specifies how many IDs to map.',
    )


class OSContainerIDMapInfo(Model):
    '''Model representing the <idmap> element in the <os> element in domain configuration.

       The `uid` and `gid` properties correspond to those specific
       sub-elements of the <idmap> element.'''
    uid: OSContainerIDMapEntry = Field(
        description='Specifies ID mapping parameters for user IDs.',
    )
    gid: OSContainerIDMapEntry = Field(
        description='Specifies ID mapping parameters for group IDs.',
    )


class _BaseOSInfo(Model):
    arch: NonEmptyString | None = Field(
        default=None,
        description='The CPU architecture to use for this domain. Accepted values vary based on the domain type.',
    )
    machine: NonEmptyString | None = Field(
        default=None,
        description='The machine type to use for this domain. Accepted values vary based on the domain type.',
    )
    type: NonEmptyString | None = Field(
        default=None,
        description='The guest type to be used with this domain. Accepted values vary based on the domain type.',
    )


class OSFirmwareInfo(_BaseOSInfo):
    '''Model representing a guest firwmare boot setup.

       `firmware` corresponds to the attribute of the same name on the
       <os> element.'''
    variant: Literal['firmware']
    firmware: NonEmptyString | None = Field(
        default=None,
        description='Specifies the type of firmware to use for auto-selection.',
    )
    loader: OSFWLoaderInfo | None = Field(
        default=None,
        description='Configuration for the guest firmware. If not specified, default firmware will be used.',
    )
    nvram: OSFWNVRAMInfo | None = Field(
        default=None,
        description="Configuration for the guest NVRAM. If this is specified, the 'loader' property must also be specified.",
    )

    @model_validator(mode='after')
    def check_nvram(self: Self) -> Self:
        if self.nvram is not None and self.loader is None:
            raise ValueError('NVRAM may only be specified if loader is also specified.')

        return self


class OSHostBootInfo(_BaseOSInfo):
    '''Model representing a host bootloader setup, such as might be used witn Xen.'''
    variant: Literal['host']
    bootloader: FilePath = Field(
        description='Path to the bootloader executable on the host system.',
    )
    bootloader_args: str | None = Field(
        default=None,
        description='Arguments to pass to the bootloader.',
    )


class OSDirectBootInfo(_BaseOSInfo):
    '''Model representing a direct kernel boot setup.'''
    variant: Literal['direct']
    kernel: FilePath = Field(
        description='Path to the guest kernel image on the host system.',
    )
    loader: FilePath | None = Field(
        default=None,
        description='Path to firmware image to use to initialize the guest hardware.',
    )
    initrd: FilePath | None = Field(
        default=None,
        description='Path to the guest initrd/initramfs image on the host system.',
    )
    cmdline: str | None = Field(
        default=None,
        description='Command line arguments to pass to the guest kernel.',
    )
    dtb: FilePath | None = Field(
        default=None,
        description='Path to the guest device tree binary on the host system.',
    )


class OSContainerBootInfo(_BaseOSInfo):
    '''Model representing a container boot setup.'''
    variant: Literal['container']
    init: FilePath = Field(
        description='Absolute path within the container to the init process for the container.',
    )
    initargs: Sequence[str] = Field(
        default_factory=list,
        description='List of arguments to pass to the init process on startup.',
    )
    initenv: Mapping[NonEmptyString, str | int | float] = Field(
        default_factory=dict,
        description='Mapping of environment variables to use when launching the init process.',
    )
    initdir: Annotated[str, Field(pattern=r'^/.*$')] | None = Field(
        default=None,
        description='Working directory in the container to start the init process in.',
    )
    inituser: NonEmptyString | Annotated[int, Field(ge=0)] | None = Field(
        default=None,
        description='User to start the init process as, either specified as a user name or a numeric UID.',
    )
    initgroup: NonEmptyString | Annotated[int, Field(ge=0)] | None = Field(
        default=None,
        description='Group to start the init process as, either specified as a group name or a numeric GID.',
    )
    idmap: OSContainerIDMapInfo | None = Field(
        default=None,
        description='Configuration for mapping of host UIDs and GIDs to container UIDs and GIDs.',
    )


class OSTestBootInfo(Model):
    '''Model representing boot configuration for a 'test' type domain.'''
    variant: Literal['test']
    arch: NonEmptyString = Field(
        description='The CPU architecture to use for this domain. Accepted values vary based on the domain type.',
    )


class ClockTimerInfo(Model):
    '''Model representing a timer configuration within the clock configurationf or a domain.

       All properties correspond directly to the attributes of the same
       name for the resultant <timer /> element.'''
    name: Literal['platform', 'hpet', 'kvmclock', 'pit', 'rtc', 'tsc', 'hypervclock', 'armvtimer'] = Field(
        description='The name of the timer to configure. Supported timers depend on the hypervisor, ' +
                    'the domain type, and the domain CPU architecture.',
    )
    track: Literal['boot', 'guest', 'wall', 'realtime'] | None = Field(
        default=None,
        description='Indicates what time the timer should track.',
    )
    tickpolicy: Literal['delay', 'catchup', 'merge', 'discard'] | None = Field(
        default=None,
        description='Indicates how the timer should handle missed ticks.',
    )
    present: V_YesNo | None = Field(
        default=None,
        description='Whether or not the timer should be enabled. If not specified, the timer is implicitly enabled.',
    )


class _BaseClock(Model):
    '''Shared fields for all clock configurations.'''
    timers: Sequence[ClockTimerInfo] = Field(
        default_factory=list,
        description='A list of clock timer configuration items.',
    )


class ClockUTC(_BaseClock):
    '''Model representing a clock configured to track UTC.'''
    offset: Literal['utc']


class ClockLocal(_BaseClock):
    '''Model representing a clock configured to track local time.'''
    offset: Literal['localtime']


class ClockTimezone(_BaseClock):
    '''Model representing a clock configured to track a specific timezone.'''
    offset: Literal['timezone']
    tz: NonEmptyString = Field(
        description='The name of the timezone to track. The value should match an entry in the host system’s timezone database.',
    )


class ClockVariable(_BaseClock):
    '''Model representing a clock configured to track time based on what the guest sets.'''
    offset: Literal['variable']
    basis: Literal['utc', 'localtime'] = Field(
        default='utc',
        description='Controls what offset to base the variable time tracking on.',
    )
    adjustment: int = Field(
        default=0,
        description='The number of seconds of offset from the time specified by the basis property.',
    )


class ClockAbsolute(_BaseClock):
    '''Model representing a clock configured to always have the same time at guest startup.'''
    offset: Literal['absolute']
    start: V_Timestamp = Field(
        description='An timestamp representing the exact time the clock should start at on each guest boot.',
    )


class FeaturesHyperVSpinlocks(Model):
    '''Model representing Hyper-V spinlock config for domain features.

       The `state` and `retries` properties correspond to the attributes
       of the same name on the <spinlocks /> element.'''
    state: V_OnOff = Field(
        description='Whether Hyper-V spinlocks should be on or off.',
    )
    retries: int | None = Field(
        default=None,
        ge=4096,
        description='How many retries to use with Hyper-V spinlocks. If not specified, the hypervisor default will be used.',
    )


class FeaturesHyperVSTimer(Model):
    '''Model representing Hyper-V stimer config for domain features.

       The `state` and `direct` properties correspond to the attributes
       of the same name on the <stimer /> element.'''
    state: V_OnOff = Field(
        description='Whether or not the Hyper-V stimer feature should be enabled.',
    )
    direct: V_OnOff | None = Field(
        default=None,
        description='Whether direct mode should be enabled for the Hyper-V stimer feature or not.',
    )


class FeaturesHyperVVendorID(Model):
    '''Model representing Hyper-V vendor_id config for domain features.

       The `state` and `value` properties correspond to the attributes
       of the same name on the <vendor_id /> element.'''
    state: V_OnOff = Field(
        description='Whether or not the Hyper-V vendor ID should be exposed to the guest.',
    )
    value: Annotated[str, Field(min_length=1, max_length=12)] | None = Field(
        default=None,
        description='The vendor ID that should be exposed to the guest.',
    )


class FeaturesHyperVInfo(Model):
    '''Model representing Hyper-V features configuration for a domain.

       `mode` corresponds to the attribute of the same name for the
       <hyperv> element. Users should not need to set it manually,
       as the correct value will be automatically inferred based on
       whether any other properties are set or not.

       Other properties correspond to the elements of the same name
       that would be put in the <hyperv> element in the config.'''
    mode: Literal['passthrough', 'custom'] = Field(
        default='passthrough',
        description='What mode to use for handling Hyper-V features. This will be set to the ' +
                    'correct value automatically and should not need to be specified manually.',
    )
    avic: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V AVIC feature should be enabled. If not specified, the hypervisor default will be used.',
    )
    evmcs: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V Enlightened VMCS feature should be enabled. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    frequencies: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V frequency MSRs should be enabled. If not specified, the hypervisor default will be used.',
    )
    ipi: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V PV IPI feature should be enabled. If not specified, the hypervisor default will be used.',
    )
    reenlightenment: V_OnOff | None = Field(
        default=None,
        description='Whether or not re-enlightenment notification on migration should be enabled. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    relaxed: V_OnOff | None = Field(
        default=None,
        description='Whether or not Hyper-V relaxed timer constraints should be enabled. If not specified, the hypervisor default will be used.',
    )
    reset: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V hypervisor reset feature should be enabled. If not specified, the hypervisor default will be used.',
    )
    runtime: V_OnOff | None = Field(
        default=None,
        description='Whether or not Hyper-V runtime tracking should be enabled. If not specified, the hypervisor default will be used.',
    )
    spinlocks: FeaturesHyperVSpinlocks | None = Field(
        default=None,
        description='Configuration for the Hyper-V spinlocks feature. If not specified, hypervisor defaults will be used.',
    )
    stimer: FeaturesHyperVSTimer | None = Field(
        default=None,
        description='Configuration for the Hyper-V stimer feature. If not specified, hypervisor defaults will be used.',
    )
    synic: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V SynIC feature should be enabled. If not specified, the hypervisor default will be used.',
    )
    tlbflush: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V PV TLB flush feature should be enabled. If not specified, the hypervisor default will be used.',
    )
    vapic: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V virtual APIC feature should be enabled. If not specified, the hypervisor default will be used.',
    )
    vendor_id: FeaturesHyperVVendorID | None = Field(
        default=None,
        description='Configuration for the Hyper-V vendor ID feature. If not specified, hypervisor defaults will be used.',
    )
    vpindex: V_OnOff | None = Field(
        default=None,
        description='Whether or not the Hyper-V virtual processor index feature should be enabled. ' +
                    'If not specified, the hypervisor default will be used.',
    )

    @model_validator(mode='after')
    def fixup_mode(self: Self) -> Self:
        for item in self.model_fields_set:
            if item != 'mode' and getattr(self, item) is not None:
                self.mode = 'custom'
                break

        return self


class FeaturesKVMDirtyRing(Model):
    '''Model representing KVM dirty-ring config for domain features.

       The properties correspond to the equivalently named attributes
       on the <dirty-ring /> element.'''
    state: V_OnOff = Field(
        description='Whether the KVM dirty-ring feature should be enabled or not.',
    )
    size: int | None = Field(
        default=None,
        ge=1024,
        le=65536,
        description='Size of the KVM dirty ring buffer. Must be a power of two. If not specified, the hypervisor default will be used.',
    )

    @field_validator('size')
    @classmethod
    def check_size(cls: type[FeaturesKVMDirtyRing], v: int | None, info: ValidationInfo) -> int | None:
        if v is not None and v > 0 and (v & (v - 1)) != 0:
            raise ValueError('"size" property must be a power of 2 between 1024 and 65536')

        return v


class FeaturesKVMInfo(Model):
    '''Model representing KVM features configuration for a domain.

       The properties correspond to the equivalently named elements that
       can be found in the <kvm> element in the domain configuration.'''
    dirty_ring: FeaturesKVMDirtyRing | None = Field(
        default=None,
        description='Configuration for the KVM dirty-ring feature. If not present, hypervisor defaults will be used.',
    )
    hidden: V_OnOff | None = Field(
        default=None,
        description='Whether to or not to hide KVM from MSR-based discovery. If not present, the hypervisor default will be used.',
    )
    hint_dedicated: V_OnOff | None = Field(
        default=None,
        description='Hint to the guest that it’s vCPUs are pinned to host CPUs. If not present, the hypervisor default will be used.',
    )
    poll_control: V_OnOff | None = Field(
        default=None,
        description='Whether or not the KVM poll-control feature should be enabled. If not present, the hypervisor default will be used.',
    )
    pv_ipi: V_OnOff | None = Field(
        default=None,
        description='Whether or not the KVM PV IPI feature should be enabled. If not present, the hypervisor default will be used.',
    )


class FeaturesXenPassthrough(Model):
    '''Model representing Xen passthrough config for domain features.

       The properties correspond to the equivalently named attributes
       on the <passthrough /> element.'''
    state: V_OnOff = Field(
        description='Whether or not to enable Xen IOMMU passthrough mappings.',
    )
    mode: Literal['sync_pt', 'share_pt'] | None = Field(
        default=None,
        description='Indicates the operational mode of Xen IOMMU passthrough support. If not specified, the hypervisor default will be used.',
    )


class FeaturesXenInfo(Model):
    '''Model representing Xen features configuration for a domain.

       The properties correspond to the equivalently named elements that
       can be found in the <xen> element in the domain configuration.'''
    e820_host: V_OnOff | None = Field(
        default=None,
        description='Whether to expose the host e820 memory mappings to a PV guest domain or not. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    passthrough: FeaturesXenPassthrough | None = Field(
        default=None,
        description='Configuration for Xen IOMMU passthrough. If not specified, the hypervisor defaults will be used.',
    )


class FeaturesTCGInfo(Model):
    '''Model representing TCG features configuration for a domain.

       The `tb_cache` property indicates the size in mibibytes (not
       bytes or megabytes) of the TCG translation block cache.'''
    tb_cache: int | None = Field(
        default=None,
        gt=0,
        description='THe size of the TCG translation block cache to use, specified in mibibytes. ' +
                    'If not specified, the hypervisor default will be used.',
    )


class FeaturesAPICInfo(Model):
    '''Model representing APIC features configuration for a domain.

       The `eoi` property corresponds to the attribute of the same name
       on the <apic /> element in the domain configuration. A value of
       None for that property indicates that an <apic /> element should
       be present, but should not have any attributes.'''
    eoi: V_OnOff | None = Field(
        default=None,
        description='Whether End Of Interrupt functionality should be available to the guest. If not specified, the hypervisor default will be used.',
    )


class FeaturesGICInfo(Model):
    '''Model representing GIC features configuration for a domain.

       The `version` property corresponds to the attribute of the same
       name on the <gic /> element in the domain configuration. A value
       of None for that property indicates that an <gic /> element should
       be present, but should not have any attributes.'''
    version: Literal[2, '2', 3, '3', 'host'] | None = Field(
        default=None,
        description='The GIC version to be used for this guest. If not specified, the hypervisor default will be used.',
    )


class FeaturesIOAPICInfo(Model):
    '''Model representing IOAPIC features configuration for a domain.

       The `driver` property corresponds to the attribute of the same
       name on the <ioapic /> element in the domain configuration. A
       value of None for that property indicates that an <ioapic />
       element should be present, but should not have any attributes.'''
    driver: Literal['kvm', 'qemu'] | None = Field(
        default=None,
        description='Specifies the driver mode to use for the guest IO-APIC. If not specified, the hypervisor default will be used.',
    )


class FeaturesSMMConfig(Model):
    '''Model representing SMM configuration for a domain.

       The properties correspond to the properties of the same name on
       the <smm /> element in the domain XML.'''
    state: V_OnOff = Field(
        description='Specifies whether SMM support should be enabled for the guest or not.',
    )
    tseg: int | None = Field(
        default=None,
        gt=0,
        description='Specifies the size of the SMM extended TSEG in bytes. This should be left unspecified ' +
                    'unless the domain has hundreds of vCPUs or a very large address space (in excess of 1 TiB). ' +
                    'If not specified, the hypervisor default will be used.',
    )


class FeaturesCapabilities(Model):
    '''Model representing capabilities configuration for a domain.

       The `policy` property corresponds to the attribute of the same
       name on the <capabilities> element in the domain configuration.

       The `modify` property is a mapping of capability names to
       capability states, with each entry corresponding to an element
       under the <capabilities> element.'''
    policy: Literal['default', 'allow', 'deny'] = Field(
        description='Specify the default policy for domain capabilities.',
    )
    modify: Mapping[NonEmptyString, V_OnOff] = Field(
        default_factory=dict,
        description='Specify individual overrides for the default policy. Keys should be capability names, values should indicate whether that ' +
                    'capability will be enabled for the domain or not. If not specified or left empty, the default policy will be followed for ' +
                    'all capabilities.',
    )


class FeaturesInfo(Model):
    '''Model representing the contents of the <features> element in domain configuration.

       The individual properties correspond to the elements of the
       equivalent name found in the <features> element in the domain
       configuration.'''
    acpi: V_OnOff | None = Field(
        default=None,
        description='Whether ACPI should be enabled for the domain or not. If not specified, the hypervisor default will be used.',
    )
    apic: FeaturesAPICInfo | None = Field(
        default=None,
        description='Configuration for the domain APIC. If not specified, hypervisor defaults will be used.',
    )
    async_teardown: V_OnOff | None = Field(
        default=None,
        description='Whether asynchronous teardown should be enabled for the domain or not. If not specified, the hypervisor default will be used.',
    )
    caps: FeaturesCapabilities | None = Field(
        default=None,
        description='Configuration for the domain capabilities. If not specified, hypervisor defaults will be used.',
    )
    gic: FeaturesGICInfo | None = Field(
        default=None,
        description='Configuration for the domain GIC. If not specified, hypervisor defaults will be used.',
    )
    hap: V_OnOff | None = Field(
        default=None,
        description='Whether Hardware Assisted Paging should be enabled for the domain or not. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    htm: V_OnOff | None = Field(
        default=None,
        description='Whether HTM should be enabled for the domain or not. If not specified, the hypervisor default will be used.',
    )
    hyperv: FeaturesHyperVInfo | None = Field(
        default=None,
        description='Configuration for Hyper-V features. If not specified, hypervisor defaults will be used.',
    )
    kvm: FeaturesKVMInfo | None = Field(
        default=None,
        description='Configuration for KVM features. If not specified, hypervisor defaults will be used.',
    )
    pae: V_OnOff | None = Field(
        default=None,
        description='Whether PAE should be enabled for the domain or not. If not specified, the hypervisor default will be used.',
    )
    pmu: V_OnOff | None = Field(
        default=None,
        description='Whether the guest PMU should be enabled or not. If not specified, the hypervisor default will be used.',
    )
    pvspinlock: V_OnOff | None = Field(
        default=None,
        description='Whether pvspinlocks should be enabled for the domain or not. If not specified, the hypervisor default will be used.',
    )
    smm: FeaturesSMMConfig | None = Field(
        default=None,
        description='Configuration for system management mode for the domain. If not specified, hypervisor defaults will be used.',
    )
    tcg: FeaturesTCGInfo | None = Field(
        default=None,
        description='Configuration for TCG features. If not specified, hypervisor defaults will be used.',
    )
    vmcoreinfo: V_OnOff | None = Field(
        default=None,
        description='Whether vmcoreinfo should be enabled for the domain or not. If not specified, the hypervisor default will be used.',
    )
    vmport: V_OnOff | None = Field(
        default=None,
        description='Whether VMWare IO port emulation should be enabled for the domain or not. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    xen: FeaturesXenInfo | None = Field(
        default=None,
        description='Configuration for Xen features. If not specified, hypervisor defaults will be used.',
    )


class ControllerDriverInfo(Model):
    '''Model representing a driver element in a controller device entry.'''
    queues: int | None = Field(
        default=None,
        gt=0,
        description='Specify the number of queues that the controller should expose. For best performance, ' +
                    'this should match the number of vcpus assigned to the domain. If not specified, the hypervisor default will be used.',
    )
    cmd_per_lun: int | None = Field(
        default=None,
        gt=0,
        description='Specify the maximum number of commands that can be queued per LUN for host-controlled devices on a SCSI controller. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    max_sectors: int | None = Field(
        default=None,
        gt=0,
        description='Specify the maximum amount of data that can be transferred in a single command, measured in 512-byte sectors. ' +
                    'If not specified, the hypervisor default will be used.',
    )


class _BaseController(Model):
    '''Base model for other controller models.'''
    index: int | None = Field(
        default=None,
        ge=0,
        description='Indicates the enumeration order for the controller. ' +
                    'If left unspecified, the lowest unused index for the controller type will be auto-assigned.',
    )


class SimpleController(_BaseController):
    '''A simple controller device definition that supports no additional configuration.'''
    type: Literal['fdc', 'sata', 'ccid']


class XenBusController(_BaseController):
    '''A Xen Bus controller device.'''
    type: Literal['xenbus']
    maxEventChannels: int | None = Field(
        default=None,
        gt=0,
        description='Specifies the number of event channels the controller provides. ' +
                    'If not specified, the hypervisor default will be used.',
    )
    maxGrantFrames: int | None = Field(
        default=None,
        gt=0,
        description='Specifies the number of grant frames the controller provides. ' +
                    'If not specified, the hypervisor default will be used.',
    )


class _ModelController(_BaseController):
    '''Base model for controllers that support a 'model' attribute.'''
    model: NonEmptyString | None = Field(
        default=None,
        description='Specifies the model of controller to use. If left unspecified, the hypervisor default will be used.',
    )


class IDEController(_ModelController):
    '''An IDE controller device.'''
    type: Literal['ide']


class SCSIController(_ModelController):
    '''A SCSI controller device.'''
    type: Literal['scsi']
    driver: ControllerDriverInfo | None = Field(
        default=None,
        description='Driver configuration for the SCSI controller.',
    )


class USBController(_ModelController):
    '''A USB controller device.'''
    type: Literal['usb']
    ports: int | None = Field(
        default=None,
        gt=0,
        description='Specifies the number of ports that should be available on this USB controller. ' +
                    'If left unspecified, the hypervisor default will be used.',
    )


class VirtIOSerialController(_ModelController):
    '''A VirtIO serial controller device.'''
    type: Literal['virtio-serial']
    ports: int | None = Field(
        default=None,
        gt=0,
        description='Specifies the number of ports that should be available on this controller. ' +
                    'If left unspecified, the hypervisor default will be used.',
    )
    vectors: int | None = Field(
        default=None,
        gt=0,
        description='Specifies the number of vectors that should be available on this controller. ' +
                    'If left unspecified, the hypervisor default will be used.',
    )


ControllerDevice = Annotated[
    SimpleController | XenBusController | IDEController | SCSIController | USBController | VirtIOSerialController,
    Field(
        discriminator='type',
    )
]


class DiskVolumeSrcInfo(Model):
    '''Model representing a disk device volume source.'''
    pool: NonEmptyString = Field(
        description='The name of the storage pool the volume backing the disk is in.',
    )
    volume: NonEmptyString = Field(
        description='The name of the volume backing the disk.',
    )


class DiskTargetInfo(Model):
    '''Model representing a disk device target.'''
    dev: FilePath = Field(
        description='A device identifier indicating how the disk should enumerate in the guest.',
    )
    addr: PCIAddress | DriveAddress | None = Field(
        default=None,
        description='The exact address to use for the disk. Possible types are limited by the bus type. ' +
                    'If this property is specified, the bus property must also be specified. If not specified, libvirt will infer a sane default.',
    )
    bus: NonEmptyString | None = Field(
        default=None,
        description='The bus type to use when exposing the disk to the guest. If not specified, libvirt will infer a sane default.',
    )
    removable: V_OnOff | None = Field(
        default=None,
        description="Whether the disk should be presented as removable or not. Only supported for bus types 'usb' and 'scsi'. " +
                    'If not specified, the disk will be presented as non-removable if possible.',
    )
    rotation_rate: int | None = Field(
        default=None,
        gt=0,
        lt=65535,
        description='The rotation rate to report to the guest for the disk. Must be either 1 (which indicates non-rotational media) or a number ' +
                    'between 1024 and 65534 inclusive. If not specified, the hypervisor default will be used.',
    )

    @model_validator(mode='after')
    def check_addr(self: Self) -> Self:
        if self.addr is not None:
            if self.bus is None:
                raise ValueError('Disk target address may only be specified if a target bus is specified.')

            joiner = '" or "'
            valid_bus = set()

            match self.addr:
                case PCIAddress():
                    valid_bus = {'virtio', 'xen'}
                    addr_type = 'PCI'
                case DriveAddress():
                    valid_bus = {'scsi', 'ide', 'usb', 'sata', 'sd'}
                    addr_type = 'Drive'
                case _:
                    raise RuntimeError

            if self.bus not in valid_bus:
                raise ValueError(f'{addr_type} addresses for disk targets are only supported for a bus of "{joiner.join(valid_bus)}".')

        return self

    @model_validator(mode='after')
    def check_removable(self: Self) -> Self:
        if self.removable is not None and self.bus not in {'scsi', 'usb'}:
            raise ValueError('"removable" property may only be specified for a bus of "scsi" or "usb".')

        return self


class _BaseDisk(Model):
    '''Base model for disk devices.'''
    boot: int | None = Field(
        default=None,
        gt=0,
        description='The boot device index for the disk. If not specified, the disk will not be considered for booting.',
    )
    device: Literal['disk', 'floppy', 'cdrom', 'lun'] | None = Field(
        default='disk',
        description='The type of disk device to expose to the guest.',
    )
    readonly: V_YesNo = Field(
        default=False,
        description='Whether the disk should be read-only.',
    )
    snapshot: Literal['internal', 'external', 'manual', 'no'] | None = Field(
        default=None,
        description='The snapshotting mode for the disk. If not specified, the hypervisor default will be used.',
    )
    target: DiskTargetInfo = Field(
        description='Configuration for how the disk is presented to the guest.',
    )


class _DiskStartupMixin(Model):
    '''Mixin to add startup property to a disk device model.'''
    startup: Literal['mandatory', 'requisite', 'optional'] | None = Field(
        default=None,
        description='Startup handling behavior for this disk. Equivalent to the startuPolicy attribute on the <source /> element.',
    )


class FileDisk(_BaseDisk, _DiskStartupMixin):
    '''A disk device backed by a disk image in a file on the host.'''
    type: Literal['file']
    src: FilePath = Field(
        description='The path to the disk image to use for this disk.',
    )


class BlockDisk(_BaseDisk):
    '''A simple disk device backed by a block device on the host.'''
    type: Literal['block']
    src: FilePath = Field(
        description='The path to the block device to use for this disk.',
    )


class VolumeDisk(_BaseDisk, _DiskStartupMixin):
    '''A disk device backed by a volume in a libvirt storage pool.'''
    type: Literal['volume']
    src: DiskVolumeSrcInfo = Field(
        description='Identifies the volume to use for this disk.',
    )


DiskDevice = Annotated[
    FileDisk | BlockDisk | VolumeDisk,
    Field(
        disciminator='type',
    )
]


class FilesystemDriverInfo(Model):
    '''Model representing a filesystem device driver in domain config.'''
    type: NonEmptyString = Field(
        description='The driver type to use. Supported values vary based on the hypervisor being used and the filesystem type.',
    )
    format: NonEmptyString | None = Field(
        default=None,
        description='The filesystem type to use. Only supported for certain driver types. Supported values depend on the driver type.',
    )
    queues: int | None = Field(
        default=None,
        gt=0,
        description='The number of queues to provide for a virtiofs type filesystem.',
    )
    wrpolicy: NonEmptyString | None = Field(
        default=None,
        description='Specify the host-side write-caching policy for the filesystem. Only supported for some driver types.',
    )


class Filesystem(Model):
    '''Model representing a filesystem device in domain config.'''
    type: Literal['mount', 'template', 'file', 'block', 'ram', 'bind'] = Field(
        description='The type of filesystem interface to use. Supported interfaces depend on the domain type.',
    )
    source: NonEmptyString = Field(
        description='Filesystem source. Exact meaning depends on the filesystem type and driver type.',
    )
    target: NonEmptyString = Field(
        description='Filesystem target identifier. Meaning depends on filesystem type and driver type.',
    )
    accessmode: Literal['passthrough', 'mapped', 'squash'] | None = Field(
        default=None,
        description='How to handle permissions for the filesystem. Only supported by some driver types.',
    )
    dmode: FileMode | None = Field(
        default=None,
        description="Directory permissions to use for newly created directories with an accessmode of 'mapped'.",
    )
    fmode: FileMode | None = Field(
        default=None,
        description="File permissions to use for newly created files with an accessmode of 'mapped'.",
    )
    driver: FilesystemDriverInfo | None = Field(
        default=None,
        description='Host driver configuration for the filesystem. If not specified, hypervisor defaults will be used.',
    )
    multidev: Literal['default', 'remap', 'forbid', 'warn'] | None = Field(
        default=None,
        description='Configure handling of filesystems exposing multiple device IDs. Only supported for 9P-based filesystems on QEMU domains.',
    )
    readonly: V_YesNo = Field(
        default=False,
        description='Whether the filesystem should be read-only for the guest or not.',
    )
    src_type: NonEmptyString | None = Field(
        default=None,
        description='The type of source identifier for this filesystem. Most filesystem and driver combinations only support a single source type, ' +
                    'in which case this will be handled automatically. Users should only need to specify this manually when using specific driver ' +
                    'types that support more than one type of source.',
    )

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


class NetworkVPort(Model):
    '''Model representing a virtualport element for a network interface.'''
    type: NonEmptyString | None = Field(
        default=None,
        description='The type of virtualport to configure.',
    )
    instanceid: NonEmptyString | None = Field(
        default=None,
        description='The instance ID for the virtual port.',
    )
    interfaceid: NonEmptyString | None = Field(
        default=None,
        description='The interface ID for the virtual port.',
    )
    managerid: NonEmptyString | None = Field(
        default=None,
        description='The manager ID for the virtual port.',
    )
    profileid: NonEmptyString | None = Field(
        default=None,
        description='The profile ID for the virtual port.',
    )
    typeid: NonEmptyString | None = Field(
        default=None,
        description='The type ID for the virtual port.',
    )
    typeidversion: int | None = Field(
        default=None,
        gt=0,
        description='The type ID version for the virtual port.',
    )


class NetworkIPv4Info(Model):
    '''Model representing an IPv4 configuration for a user network driver.'''
    address: IPv4Address = Field(
        description='The IP address to associate with the interface.',
    )
    prefix: int = Field(
        ge=1,
        le=31,
        description='The prefix length for the IP address.',
    )


class NetworkIPv6Info(Model):
    '''Model representing an IPv6 configuration for a user network driver.'''
    address: IPv6Address = Field(
        description='The IP address to associate with the interface.',
    )
    prefix: int = Field(
        ge=1,
        le=127,
        description='The prefix length for the IP address.',
    )


class _BaseNetwork(Model):
    '''Base model with shared properties for all network types.'''
    boot: int | None = Field(
        default=None,
        gt=0,
        description='The boot device index for the interface. If not specified, the interface will not be considered for booting.',
    )
    mac: MacAddress | None = Field(
        default=None,
        description='The MAC address to provide for the interface. If not specified, the hypervisor will assign a MAC address itself.',
    )
    target: NonEmptyString | None = Field(
        default=None,
        description='Target identifier for device enumeration. If not specified, hypervisor defaults will be used.',
    )


class _NetworkVPortMixin(Model):
    '''Mixin for network types with virtualport support.'''
    virtualport: NetworkVPort | None = Field(
        default=None,
        description='Virtual port configuration for the network interface.',
    )


class VirtualInterface(_BaseNetwork, _NetworkVPortMixin):
    '''Model representing a network interface connected to a libvirt-managed network.'''
    type: Literal['network']
    src: NonEmptyString = Field(
        description='The libvirt network name to connect the interface to.',
    )


class BridgeInterface(_BaseNetwork, _NetworkVPortMixin):
    '''Model representing a network interface connected to an externally managed software bridge device.'''
    type: Literal['bridge']
    src: NonEmptyString = Field(
        description='The bridge device name to connect the interface to.',
    )


class DirectInterface(_BaseNetwork, _NetworkVPortMixin):
    '''Model representing a network interface bound directly to a host network interface.'''
    type: Literal['direct']
    src: NonEmptyString = Field(
        description='The host device name to connect the interface to.',
    )
    mode: Literal['vepa', 'bridge', 'private', 'passthrough'] | None = Field(
        default=None,
        description='The mode to use when binding to the host device.',
    )


class UserInterface(_BaseNetwork):
    '''Model representing a network interface linked to a transparent userspace proxy.'''
    type: Literal['user']
    ipv4: NetworkIPv4Info | None = Field(
        default=None,
        description='The IPv4 address to associate with the interface.',
    )
    ipv6: NetworkIPv6Info | None = Field(
        default=None,
        description='The IPv6 address to associate with the interface.',
    )

    @model_validator(mode='after')
    def check_addrs(self: Self) -> Self:
        if self.ipv4 is None and self.ipv6 is None:
            raise ValueError('At least one address configuration must be specified for user type network interfaces.')

        return self


class NullInterface(_BaseNetwork):
    '''Model representing a network interface that is not connected to anything.'''
    type: Literal['null', None]


NetworkInterface = Annotated[VirtualInterface | BridgeInterface | DirectInterface | NullInterface | UserInterface, Field(discriminator='type')]


class InputSource(Model):
    '''Model representing an input device source for an evdev device.'''
    dev: FilePath = Field(
        description='The host device to connect to.',
    )
    grab: Literal['all'] | None = Field(
        default=None,
        description='Specifies input device grab handling.',
    )
    repeat: V_OnOff | None = Field(
        default=None,
        description='Specifies the auto-repeat mode.',
    )
    grabToggle: NonEmptyString | None = Field(
        default=None,
        description='The key sequence used to toggle input event grabbing.',
    )


class _BaseInput(Model):
    '''Base model with shared attributes for all input devices.'''
    bus: Literal['usb', 'ps2', 'virtio', 'xen'] | None = Field(
        default=None,
        description='The bus to connect the input device to in the guest. If not specified, a sane default will be used.',
    )
    model: NonEmptyString | None = Field(
        default=None,
        description='The VirtIO device model to use for a VirtIO input device.',
    )


class SimpleInputDevice(_BaseInput):
    '''Represents a simple input device for the domain.'''
    type: Literal['keyboard', 'mouse', 'tablet']


class PassthroughInputDevice(_BaseInput):
    '''Represents a passthrough input device for the domain.'''
    type: Literal['passthrough']
    src: FilePath = Field(
        description='The host device to pass through to the guest.',
    )


class EvdevInputDevice(_BaseInput):
    '''Represents an evdev input device for the domain.'''
    type: Literal['evdev']
    src: InputSource = Field(
        description='Host device configuration info.',
    )


InputDevice = Annotated[SimpleInputDevice | PassthroughInputDevice | EvdevInputDevice, Field(discriminator='type')]


class AddressGraphicsListener(Model):
    '''Represents a graphics listener listening on a specific network address.'''
    type: Literal['address']
    listen: IPv4Address | IPv6Address = Field(
        description='The address to listen on.',
    )


class NetworkGraphicsListener(Model):
    '''Represents a graphics listener listening on a libvirt-managed network.'''
    type: Literal['network']
    listen: NonEmptyString = Field(
        description='The libvirt network to listen on.',
    )


class SocketGraphicsListener(Model):
    '''Represents a grpahics listener listening on a UNIX domain socket on the host.'''
    type: Literal['socket']
    listen: FilePath = Field(
        description='The socket to listen on.',
    )


class NullGraphicsListener(Model):
    '''Represents a graphics listener that is not connected to anything.'''
    type: Literal['none']


GraphicsListener = Annotated[AddressGraphicsListener | NetworkGraphicsListener | SocketGraphicsListener | NullGraphicsListener, Field(
    discriminator='type',
)]


class _RemoteGraphics(Model):
    '''Base model for graphics output interfaces that utilizes a remote connection.'''
    listeners: Sequence[GraphicsListener] = Field(
        default_factory=list,
        description='A list of listeners for the device.',
    )
    port: NetPort | None = Field(
        default=None,
        description="The port to listen on. If both this and 'autoport' are not specified, a hypervisor-specific default will be used.",
    )
    autoport: V_YesNo | None = Field(
        default=None,
        description="Whether to auto-assign a port for the device or not. Mutually exclusive with the 'port' property.",
    )
    passwd: str | None = Field(
        default=None,
        description='Specifies a password for remote users to connect to the graphics device.',
    )
    passwdValidTo: V_Timestamp | None = Field(
        default=None,
        description='Specifies an expiration date and time for the password. Only supported if a password is specified. ' +
                    'If specified as a string, this should be an ISO 8601 compliant timestamp. If no timezone is specified, ' +
                    'it will be assumed to have a timezone of UTC. If only a date is specified, the time will be set to midnight of that day.',
    )
    connected: Literal['keep', 'disconnect', 'fail'] | None = Field(
        default=None,
        description='Specifies how to handle connected users when the password is changed or expires. Only supported if a password is specified.',
    )

    @model_validator(mode='after')
    def check_port(self: Self) -> Self:
        if self.port is not None and self.autoport:
            raise ValueError('If autoport is enabled, a port may not be specified.')

        return self

    @model_validator(mode='after')
    def check_passwd_valid(self: Self) -> Self:
        if self.passwdValidTo is not None and self.passwd is None:
            raise ValueError('Password validity limit may only be specified if a password is also specified.')

        return self

    @model_validator(mode='after')
    def check_connected(self: Self) -> Self:
        if self.connected is not None and self.passwd is None:
            raise ValueError('Password change handling may only be specified if a password is also specified.')

        return self


class _KeymapGraphicsMixin(Model):
    '''Base model for graphics devices that allow specifying a keymap.'''
    keymap: NonEmptyString | None = Field(
        default=None,
        description='Specifies the keymap to use for VNC connections. If not specified, the hypervisor default will be used.',
    )


class VNCGraphics(_RemoteGraphics, _KeymapGraphicsMixin):
    '''A VNC connected graphics output device.'''
    type: Literal['vnc']
    socket: FilePath | None = Field(
        default=None,
        description='Path to a local UNIX socket to listen on instead of listening on a netwokr port.',
    )
    websocket: int | None = Field(
        default=None,
        ge=-1,
        lt=65536,
        description='Port number to use for VNC WebSocket connections. A value of -1 indicates automatic assignment.',
    )
    sharePolicy: Literal['allow-exclusive', 'force-shared', 'ignore'] | None = Field(
        default=None,
        description='Specifies the policy for handling of shared-mode connections. If not specified, the hypervisor default will be used.',
    )
    powerControl: V_YesNo | None = Field(
        default=None,
        description='Enables or disables power control features for the VNC client.',
    )


class SPICEGraphics(_RemoteGraphics, _KeymapGraphicsMixin):
    '''A SPICE connected graphics output device.'''
    type: Literal['spice']
    tlsPort: int | None = Field(
        default=None,
        gt=0,
        lt=65536,
        description='Port number to listen on for TLS connections. If not specified, TLS connections will not be enabled.',
    )
    defaultMode: Literal['secure', 'insecure', 'any'] | None = Field(
        default=None,
        description='The default channel security policy. If not specified, the hypervisor default will be used.',
    )
    channels: Mapping[str, Literal['secure', 'insecure']] = Field(
        default_factory=dict,
        description='Overrides for the defaault channel policy. Keys are channel names, ' +
                    'while each value is the security policy for the associated channel.',
    )


class RDPGraphics(_RemoteGraphics):
    '''An RDP connected graphics output device.'''
    type: Literal['rdp']
    multiUser: V_YesNo | None = Field(
        default=None,
        description='Whether or not to allow multiple concurrent connections.'
    )
    replaceUser: V_YesNo | None = Field(
        default=None,
        description='Whether or not new connections should replace existing ones in single-connection mode. ' +
                    "May only be specified if 'mutliUser' is explicitly disabled.",
    )

    @model_validator(mode='after')
    def check_user(self: Self) -> Self:
        if self.replaceUser is not None:
            if self.multiUser is None or self.multiUser:
                raise ValueError('The "replaceUser" property is only supported if "multiUser" mode is explicitly disabled .')

        return self


GraphicsDevice = Annotated[VNCGraphics | SPICEGraphics | RDPGraphics, Field(discriminator='type')]


class VideoDevice(Model):
    '''Model representing a GPU device in domain configuration.'''
    type: Literal['vga', 'cirrus', 'vmvga', 'xen', 'vbox', 'virtio', 'qxl', 'gop', 'bochs', 'ramfb', 'none'] = Field(
        description="The type of GPU. The special value 'none' can be used to ensure that no GPU is connected even if the " +
                    'domain would have one by default. Most domain types only support a subset of the listed types.',
    )
    vram: int | None = Field(
        default=None,
        ge=16,
        description='The amount of video RAM for the GPU, measured in kibibytes. Must be a power of 2. 16 KiB is enough for all standard VGA, ' +
                    'VESA, and Video7 text modes. 8 MiB is sufficient for almost all commonly used video output modes up to and including ' +
                    '1080p with 24-bit color. If not specified, the hypervisor default will be used, which should be sufficient for ' +
                    'almost any usage that does not involve ultra-high resolution or complex rendering requirements. Only supported ' +
                    'for some domain types.',
    )
    heads: int | None = Field(
        default=None,
        gt=0,
        description='The number of display outputs. Only supported for some GPU and hypervisor types. ' +
                    'If not specified, a single display output will be provided.',
    )
    blob: V_OnOff | None = Field(
        default=None,
        description='Whether or not blob resources should be enabled for a VirtIO GPU. Only supported for VirtIO GPUs. ' +
                    'If not specified, the hypervisor default will be used.'
    )

    @model_validator(mode='after')
    def check_vram(self: Self) -> Self:
        if self.vram is not None and (self.vram & (self.vram - 1) != 0):
            raise ValueError('VRAM amount must be a power of 2')

        return self

    @model_validator(mode='after')
    def check_blob(self: Self) -> Self:
        if self.blob is not None and self.type != 'virtio':
            raise ValueError('"blob" property is only supported on "virtio" type video devices.')

        return self


class CharDevSimpleSource(Model):
    '''Character device source that only needs a type.'''
    type: Literal['stdio', 'vc', 'null', None]


class CharDevPathSource(Model):
    '''Character device soruce connected to a specific path.'''
    type: Literal['file', 'dev', 'pipe', 'nmdm']
    path: FilePath = Field(
        min_length=1,
        description='The path to use for the device source.',
    )


class CharDevPTYSource(Model):
    '''Character device source connected to a pseudoterminal.'''
    type: Literal['pty']
    path: FilePath | None = Field(
        default=None,
        description='The pseudoterminal to connect to. If left empty, one will be auto-assigned on domain startup. ' +
                    'Most users should leave this empty.',
    )


class CharDevSocketSource(Model):
    '''Character device source connected to a UNIX socket.'''
    type: Literal['unix']
    path: FilePath = Field(
        description='The path to the socket to use.',
    )
    mode: Literal['connect', 'bind'] = Field(
        description="The mode to use. 'connect' will connect to the socket as a client, while 'bind' will listen on the socket.",
    )


class CharDevTCPSource(Model):
    '''Character device source connected to a TCP client or server.'''
    type: Literal['tcp']
    mode: Literal['connect', 'bind'] = Field(
        description="The mode to use. 'connect' will connect to a remote host, while 'bind' will listen on a local socket.",
    )
    host: Hostname | IPv4Address | IPv6Address = Field(
        description='The hostname or IP address to connect to or listen on.',
    )
    service: NetPort = Field(
        description='The port number to connect to or listen on.',
    )
    tls: V_YesNo | None = Field(
        default=None,
        description='Whether or not to enable TLS. Only supported by some hypervisors. If not specified, TLS will not be enabled.',
    )


class CharDevChannelSource(Model):
    '''Character device source connected to a SPICE channel.'''
    type: Literal['spiceport']
    channel: NonEmptyString = Field(
        description='The name of the SPICE channel to use.',
    )


CharDevSource = Annotated[
    CharDevSimpleSource |
    CharDevPathSource |
    CharDevPTYSource |
    CharDevSocketSource |
    CharDevTCPSource |
    CharDevChannelSource,
    Field(
        discriminator='type',
    )
]


class _CharDevTgtPort(Model):
    port: int = Field(
        ge=0,
        description='The port this character device corresponds to.',
    )


class ParallelDevTarget(_CharDevTgtPort):
    '''A character device target for a parallel port.'''
    category: Literal['parallel']


class SerialDevTarget(_CharDevTgtPort):
    '''A character device target for a serial port.'''
    category: Literal['serial']
    type: NonEmptyString | None = Field(
        default=None,
        description='The type of serial port to provide. If not specified, the hypervisor will infer a sane value.',
    )


class ConsoleDevTarget(_CharDevTgtPort):
    '''A character device target for a console.'''
    category: Literal['console']
    type: Literal['serial', 'virtio', 'xen', 'lxc', 'openvz', 'sclp', 'sclplm'] = Field(
        description='The type of console to provide.',
    )


class _ChannelDevTarget(Model):
    category: Literal['channel']


class NetChannelDevTarget(_ChannelDevTarget):
    '''A character device target for a network channel.'''
    type: Literal['guestfwd']
    address: IPv4Address | IPv6Address = Field(
        description='The IP address for the channel.',
    )
    port: NetPort = Field(
        description='The TCP port to use for the channel.',
    )


class _NamedChannelDevTarget(_ChannelDevTarget):
    name: NonEmptyString = Field(
        description='The name to associate with the channel.',
    )


class VirtIOChannelDevTarget(_NamedChannelDevTarget):
    '''A character device target for a VirtIO channel.'''
    type: Literal['virtio']


class XenChannelDevTarget(_NamedChannelDevTarget):
    '''A character device target for a Xen channel.'''
    type: Literal['xen']


ChannelDevTarget = Annotated[NetChannelDevTarget | VirtIOChannelDevTarget | XenChannelDevTarget, Field(discriminator='type')]
CharDevTarget = Annotated[ParallelDevTarget | SerialDevTarget | ConsoleDevTarget | ChannelDevTarget, Field(discriminator='category')]


class CharDevLog(Model):
    '''Model representing log config for a character device.'''
    file: FilePath = Field(min_length=1)
    append: V_OnOff | None = Field(default=None)


class CharacterDevice(Model):
    '''Model representing a character device in domain configuration.'''
    target: CharDevTarget = Field(
        description='The target for the character device.',
    )
    src: CharDevSource = Field(
        default_factory=lambda: CharDevPTYSource(type='pty', path=None),
        description='The source for the character device. If not specified, an auto-assigned PTY source will be used.',
    )
    log: CharDevLog | None = Field(
        default=None,
        description='Logging configuration for the character device. If not specified, no logging will be configured.',
    )


class WatchdogDevice(Model):
    '''Model representing a watchdog device in domain configuration.'''
    model: NonEmptyString = Field(
        description='The model of watchdog device to provide. Accepted values are hypervisor-dependent.',
    )
    action: Literal['reset', 'shutdown', 'poweroff', 'pause', 'none', 'dump', 'inject-nmi'] | None = Field(
        default=None,
        description='The action to take when the watchdog timer expires. If not specified, the hypervisor default will be used.',
    )


class RNGBuiltinBackend(Model):
    '''Builtin backend for RNG devices.'''
    model: Literal['builtin']


class RNGRandomBackend(Model):
    '''Backend for RNG devices that connects to a local RNG device.'''
    model: Literal['random']
    path: FilePath = Field(
        description='The path to the RNG device to use.',
    )


class RNGEGDSocketBackend(CharDevSocketSource):
    '''RNG backend that connects to EGD over a UNIX socket.'''
    model: Literal['egd']


class RNGEGDTCPBackend(CharDevTCPSource):
    '''RNG backend that connects to EGD over a TCP socket.'''
    model: Literal['egd']


RNGEGDBackend = Annotated[RNGEGDSocketBackend | RNGEGDTCPBackend, Field(discriminator='type')]
RNGBackend = Annotated[RNGBuiltinBackend | RNGRandomBackend | RNGEGDBackend, Field(discriminator='model')]


class RNGDevice(Model):
    '''Model representing an RNG device in domain configuration.'''
    model: NonEmptyString = Field(
        description='The model of RNG device to provide. Valid models depend on the underlying hypervisor.',
    )
    rate: DataRate | None = Field(
        default=None,
        description='Rate limit for reading data from the RNG device. If not specified, reading will not be rate limited.',
    )
    backend: RNGBackend = Field(
        default_factory=lambda: RNGBuiltinBackend(model='builtin'),
        description='The backend for the RNG device on the host. If not specified, the builtin backend will be used.',
    )


class _BaseTPM(Model):
    model: Literal['tpm-tis', 'tpm-crb', 'tpm-spapr', 'tpm-spapr-proxy'] | None = Field(
        default=None,
        description='The interface provided by the TPM device. If not specified, libvirt will infer a reasonable value ' +
                    'based on the domain configuration.',
    )


class PassthroughTPM(_BaseTPM):
    '''A TPM device that exposes a host TPM device to the guest.'''
    type: Literal['passthrough']
    dev: FilePath = Field(
        description='The path to the host device to pass through.',
    )


class EmulatedTPM(_BaseTPM):
    '''A TPM device provided by an emulator running on the host.'''
    type: Literal['emulator']
    encryption: UUID | None = Field(
        default=None,
        description='UUID of the libvirt secret containing the passphrase used to encrypt the TPM state. ' +
                    'If not specified, the TPM state will be stored unencrypted.',
    )
    version: Literal['1.2', '2.0'] | None = Field(
        default=None,
        description='The version of the TPM device. If not specified, libvirt will infer a sane default based on other parameters.',
    )
    persistent_state: V_YesNo = Field(
        default=False,
        description='Whether the TPM state should be kept or not when a transient domain is powered off.',
    )
    active_pcr_banks: Sequence[Annotated[str, Field(min_length=1)]] = Field(
        default_factory=list,
        description='A list of PCR banks to activate on VM startup. If not specified, active PCR banks will not be modified on startup. ' +
                    'Duplicate entries in this list will be removed automatically.',
    )

    @model_validator(mode='after')
    def dedup_active_pcr_banks(self: Self) -> Self:
        self.active_pcr_banks = list(set(self.active_pcr_banks))
        return self


TPMDevice = Annotated[PassthroughTPM | EmulatedTPM, Field(discriminator='type')]


class SimpleDevice(Model):
    '''Model reprsenting simple devices that only support a model attribute.'''
    model: NonEmptyString = Field(
        description='The model of device to provide. Accepted values vary by hypervisor and domain type.',
    )


class Devices(Model):
    '''Model representing device configuration for a domain.'''
    controllers: Sequence[ControllerDevice] = Field(
        default_factory=list,
        description='A list of controller devices for the domain.',
    )
    disks: Sequence[DiskDevice] = Field(
        default_factory=list,
        description='A list of disk devices for the domain.',
    )
    fs: Sequence[Filesystem] = Field(
        default_factory=list,
        description='A list of filesystems for the domain.',
    )
    net: Sequence[NetworkInterface] = Field(
        default_factory=list,
        description='A list of network interfaces for the domain.',
    )
    input: Sequence[InputDevice] = Field(
        default_factory=list,
        description='A list of input devices for the domain.',
    )
    graphics: Sequence[GraphicsDevice] = Field(
        default_factory=list,
        description='A list of graphics output devices for the domain.',
    )
    video: Sequence[VideoDevice] = Field(
        default_factory=list,
        description='A list of GPU devices for the domain.',
    )
    chardev: Sequence[CharacterDevice] = Field(
        default_factory=list,
        description='A list of character devices for the domain.',
    )
    watchdog: Sequence[WatchdogDevice] = Field(
        default_factory=list,
        description='A list of watchdog devices for the domain.',
    )
    rng: Sequence[RNGDevice] = Field(
        default_factory=list,
        description='A list of RNG devices for the domain.',
    )
    tpm: Sequence[TPMDevice] = Field(
        default_factory=list,
        description='A list of TPM devices for the domain.',
    )
    memballoon: Sequence[SimpleDevice] = Field(
        default_factory=list,
        description='A list of memory balloon devices for the domain.',
    )
    panic: Sequence[SimpleDevice] = Field(
        default_factory=list,
        description='A list of crash notifier devices for the domain.',
    )

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


class DomainInfo(Model):
    '''Model representing domain configuration for templating.

       Memory values should be provided in bytes unless otherwise noted.

       A value of `0` for the `vcpu` property indicates that the count
       should be inferred from topology information in the `cpu` property
       if possible, otherwise a default value should be used.'''
    name: NonEmptyString = Field(
        description='The name of the domain to create.',
    )
    type: Literal['hvf', 'kvm', 'lxc', 'vz', 'qemu', 'test', 'xen'] = Field(
        description='The domain type.',
    )
    uuid: UUID | None = Field(
        default=None,
        description='The UUID of the domain. If not specified, libvirt will auto-generate a UUID for the domain.',
    )
    genid: UUID | None = Field(
        default=None,
        description='The VM generation ID for the domain. If not specified, libvirt will auto-generate one for the domain.',
    )
    vcpu: int = Field(
        default=0,
        ge=0,
        description='The number of virtual CPUs assigned to the domain. A value of 0 indicates that a sane value should be chosen based on any ' +
                    'specified CPU topology.',
    )
    memory: int = Field(
        gt=0,
        description='The total amount of memory to assign to the domain, measured in bytes.',
    )
    memtune: MemtuneInfo | None = Field(
        default=None,
        description='Host-side memory limits for the domain. If not specified, no limits will be imposed.',
    )
    cpu: CPUInfo | None = Field(
        default=None,
        description='CPU configuration for domains that are virtual machines.',
    )
    os: OSFirmwareInfo | OSHostBootInfo | OSDirectBootInfo | OSContainerBootInfo | OSTestBootInfo = Field(
        discriminator='variant',
        description='Boot and firmware configuration for the domain.',
    )
    clock: ClockUTC | ClockLocal | ClockTimezone | ClockVariable | ClockAbsolute = Field(
        discriminator='offset',
        default=ClockUTC(offset='utc'),
        description='Clock configuration for the domain.',
    )
    features: FeaturesInfo = Field(
        default_factory=FeaturesInfo,
        description='Feature configuration for the domain.',
    )
    devices: Devices = Field(
        default_factory=Devices,
        description='Device configuration for the domain. Note that libvirt may add additional devices beyond those listed in this configuration, ' +
                    'dependent on the domain type and hypervisor.',
    )

    @computed_field  # type: ignore[misc]
    @property
    def sub_template(self: Self) -> str:
        return f'domain/{ self.type }.xml'

    @model_validator(mode='after')
    def fixup_model(self: Self) -> Self:
        if self.cpu is not None:
            if self.vcpu == 0:
                self.vcpu = self.cpu.topology.total_cpus
            else:
                self.cpu.topology.check(self.vcpu)
        else:
            self.cpu = CPUInfo()

            if self.vcpu == 0:
                self.vcpu = 1

            self.cpu.topology.check(self.vcpu)

        return self
