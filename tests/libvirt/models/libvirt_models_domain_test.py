# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.domain'''

from __future__ import annotations

import pytest

from pydantic import ValidationError

from fvirt.libvirt.models.domain import (AddressGraphicsListener, BlockDisk, BridgeInterface, CharacterDevice, CharDevChannelSource, CharDevLog,
                                         CharDevPathSource, CharDevPTYSource, CharDevSimpleSource, CharDevSocketSource, CharDevTCPSource,
                                         ClockAbsolute, ClockLocal, ClockTimerInfo, ClockTimezone, ClockUTC, ClockVariable, ConsoleDevTarget,
                                         ControllerDriverInfo, CPUInfo, CPUModelInfo, CPUTopology, DataRate, Devices, DirectInterface, DiskTargetInfo,
                                         DiskVolumeSrcInfo, DomainInfo, DriveAddress, EmulatedTPM, EvdevInputDevice, FeaturesAPICInfo,
                                         FeaturesCapabilities, FeaturesGICInfo, FeaturesHyperVInfo, FeaturesHyperVSpinlocks, FeaturesHyperVSTimer,
                                         FeaturesHyperVVendorID, FeaturesInfo, FeaturesIOAPICInfo, FeaturesKVMDirtyRing, FeaturesKVMInfo,
                                         FeaturesSMMConfig, FeaturesTCGInfo, FeaturesXenInfo, FeaturesXenPassthrough, FileDisk, Filesystem,
                                         FilesystemDriverInfo, IDEController, InputSource, MemtuneInfo, NetChannelDevTarget, NetworkGraphicsListener,
                                         NetworkIPv4Info, NetworkIPv6Info, NetworkVPort, NullGraphicsListener, NullInterface, OSContainerBootInfo,
                                         OSContainerIDMapEntry, OSContainerIDMapInfo, OSDirectBootInfo, OSFirmwareInfo, OSFWLoaderInfo, OSFWNVRAMInfo,
                                         OSHostBootInfo, OSTestBootInfo, ParallelDevTarget, PassthroughInputDevice, PassthroughTPM, PCIAddress,
                                         RDPGraphics, RNGBuiltinBackend, RNGDevice, RNGEGDSocketBackend, RNGEGDTCPBackend, RNGRandomBackend,
                                         SCSIController, SerialDevTarget, SimpleController, SimpleDevice, SimpleInputDevice, SocketGraphicsListener,
                                         SPICEGraphics, USBController, UserInterface, VideoDevice, VirtIOChannelDevTarget, VirtIOSerialController,
                                         VirtualInterface, VNCGraphics, VolumeDisk, WatchdogDevice, XenBusController, XenChannelDevTarget)

from ...shared import get_test_cases

CASES = get_test_cases('libvirt_models_domain')


@pytest.mark.parametrize('d', CASES['PCIAddress']['valid'])
def test_PCIAddress_valid(d: dict) -> None:
    '''Check validation of known-good PCI addresses.'''
    PCIAddress.model_validate(d)


@pytest.mark.parametrize('d', CASES['PCIAddress']['invalid'])
def test_PCIAddress_invalid(d: dict) -> None:
    '''Check validation of known-bad PCI addresses.'''
    with pytest.raises(ValidationError):
        PCIAddress.model_validate(d)


@pytest.mark.parametrize('d', CASES['DriveAddress']['valid'])
def test_DriveAddress_valid(d: dict) -> None:
    '''Check validation of known-good drive addresses.'''
    DriveAddress.model_validate(d)


@pytest.mark.parametrize('d', CASES['DriveAddress']['invalid'])
def test_DriveAddress_invalid(d: dict) -> None:
    '''Check validation of known-bad drive addresses.'''
    with pytest.raises(ValidationError):
        DriveAddress.model_validate(d)


@pytest.mark.parametrize('d', CASES['DataRate']['valid'])
def test_DataRate_valid(d: dict) -> None:
    '''Check validation of known-good DataRate dicts.'''
    DataRate.model_validate(d)


@pytest.mark.parametrize('d', CASES['DataRate']['invalid'])
def test_DataRate_invalid(d: dict) -> None:
    '''Check validation of known-bad DataRate dicts.'''
    with pytest.raises(ValidationError):
        DataRate.model_validate(d)


@pytest.mark.parametrize('d', CASES['MemtuneInfo']['valid'])
def test_MemtuneInfo_valid(d: dict) -> None:
    '''Check validation of known-good MemtuneInfo dicts.'''
    MemtuneInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['MemtuneInfo']['invalid'])
def test_MemtuneInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad MemtuneInfo dicts.'''
    with pytest.raises(ValidationError):
        MemtuneInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['CPUModelInfo']['valid'])
def test_CPUModelInfo_valid(d: dict) -> None:
    '''Check validation of known-good CPUModelInfo dicts.'''
    CPUModelInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['CPUModelInfo']['invalid'])
def test_CPUModelInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad CPUModelInfo dicts.'''
    with pytest.raises(ValidationError):
        CPUModelInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['CPUTopology']['valid'])
def test_CPUTopology_valid(d: dict) -> None:
    '''Check validation of known-good CPUTopology dicts.'''
    CPUTopology.model_validate(d)


@pytest.mark.parametrize('d', CASES['CPUTopology']['invalid'])
def test_CPUTopology_invalid(d: dict) -> None:
    '''Check validation of known-bad CPUTopology dicts.'''
    with pytest.raises(ValidationError):
        CPUTopology.model_validate(d)


@pytest.mark.parametrize('d, e', CASES['CPUTopology']['total_cpus'])
def test_CPUTopology_total_cpus(d: dict, e: int) -> None:
    '''Check behavior of the total_cpus property for CPUTopology instances.'''
    model = CPUTopology.model_validate(d)

    assert model.total_cpus == e


@pytest.mark.parametrize('d, v, c', CASES['CPUTopology']['check'])
def test_CPUTopology_check(d: dict, v: int, c: str | None) -> None:
    '''Check behavior of the CPUTopology.check method.'''
    model = CPUTopology.model_validate(d)

    model.check(v)

    assert model.total_cpus == v

    if c is not None:
        assert getattr(model, c) == v


def test_CPUTopology_check_bad_vcpus() -> None:
    '''Check that CPUTopology.check raises an error if passed a value less than 1.'''
    model = CPUTopology()

    with pytest.raises(ValueError):
        model.check(0)


@pytest.mark.parametrize('d', CASES['CPUInfo']['valid'])
def test_CPUInfo_valid(d: dict) -> None:
    '''Check validation of known-good CPUInfo dicts.'''
    CPUInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['CPUInfo']['invalid'])
def test_CPUInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad CPUInfo dicts.'''
    with pytest.raises(ValidationError):
        CPUInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSFWLoaderInfo']['valid'])
def test_OSFWLoaderInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSFWLoaderInfo dicts.'''
    OSFWLoaderInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSFWLoaderInfo']['invalid'])
def test_OSFWLoaderInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSFWLoaderInfo dicts.'''
    with pytest.raises(ValidationError):
        OSFWLoaderInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSFWNVRAMInfo']['valid'])
def test_OSFWNVRAMInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSFWNVRAMInfo dicts.'''
    OSFWNVRAMInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSFWNVRAMInfo']['invalid'])
def test_OSFWNVRAMInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSFWNVRAMInfo dicts.'''
    with pytest.raises(ValidationError):
        OSFWNVRAMInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSContainerIDMapEntry']['valid'])
def test_OSContainerIDMapEntry_valid(d: dict) -> None:
    '''Check validation of known-good OSContainerIDMapEntry dicts.'''
    OSContainerIDMapEntry.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSContainerIDMapEntry']['invalid'])
def test_OSContainerIDMapEntry_invalid(d: dict) -> None:
    '''Check validation of known-bad OSContainerIDMapEntry dicts.'''
    with pytest.raises(ValidationError):
        OSContainerIDMapEntry.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSContainerIDMapInfo']['valid'])
def test_OSContainerIDMapInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSContainerIDMapInfo dicts.'''
    OSContainerIDMapInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSContainerIDMapInfo']['invalid'])
def test_OSContainerIDMapInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSContainerIDMapInfo dicts.'''
    with pytest.raises(ValidationError):
        OSContainerIDMapInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSFirmwareInfo']['valid'])
def test_OSFirmwareInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSFirmwareInfo dicts.'''
    OSFirmwareInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSFirmwareInfo']['invalid'])
def test_OSFirmwareInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSFirmwareInfo dicts.'''
    with pytest.raises(ValidationError):
        OSFirmwareInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSHostBootInfo']['valid'])
def test_OSHostBootInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSHostBootInfo dicts.'''
    OSHostBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSHostBootInfo']['invalid'])
def test_OSHostBootInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSHostBootInfo dicts.'''
    with pytest.raises(ValidationError):
        OSHostBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSDirectBootInfo']['valid'])
def test_OSDirectBootInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSDirectBootInfo dicts.'''
    OSDirectBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSDirectBootInfo']['invalid'])
def test_OSDirectBootInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSDirectBootInfo dicts.'''
    with pytest.raises(ValidationError):
        OSDirectBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSContainerBootInfo']['valid'])
def test_OSContainerBootInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSContainerBootInfo dicts.'''
    OSContainerBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSContainerBootInfo']['invalid'])
def test_OSContainerBootInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSContainerBootInfo dicts.'''
    with pytest.raises(ValidationError):
        OSContainerBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSTestBootInfo']['valid'])
def test_OSTestBootInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSTestBootInfo dicts.'''
    OSTestBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSTestBootInfo']['invalid'])
def test_OSTestBootInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSTestBootInfo dicts.'''
    with pytest.raises(ValidationError):
        OSTestBootInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockTimerInfo']['valid'])
def test_ClockTimerInfo_valid(d: dict) -> None:
    '''Check validation of known-good ClockTimerInfo dicts.'''
    ClockTimerInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockTimerInfo']['invalid'])
def test_ClockTimerInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockTimerInfo dicts.'''
    with pytest.raises(ValidationError):
        ClockTimerInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockUTC']['valid'])
def test_ClockUTC_valid(d: dict) -> None:
    '''Check validation of known-good ClockUTC dicts.'''
    ClockUTC.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockUTC']['invalid'])
def test_ClockUTC_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockUTC dicts.'''
    with pytest.raises(ValidationError):
        ClockUTC.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockLocal']['valid'])
def test_ClockLocal_valid(d: dict) -> None:
    '''Check validation of known-good ClockLocal dicts.'''
    ClockLocal.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockLocal']['invalid'])
def test_ClockLocal_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockLocal dicts.'''
    with pytest.raises(ValidationError):
        ClockLocal.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockTimezone']['valid'])
def test_ClockTimezone_valid(d: dict) -> None:
    '''Check validation of known-good ClockTimezone dicts.'''
    ClockTimezone.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockTimezone']['invalid'])
def test_ClockTimezone_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockTimezone dicts.'''
    with pytest.raises(ValidationError):
        ClockTimezone.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockVariable']['valid'])
def test_ClockVariable_valid(d: dict) -> None:
    '''Check validation of known-good ClockVariable dicts.'''
    ClockVariable.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockVariable']['invalid'])
def test_ClockVariable_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockVariable dicts.'''
    with pytest.raises(ValidationError):
        ClockVariable.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockAbsolute']['valid'])
def test_ClockAbsolute_valid(d: dict) -> None:
    '''Check validation of known-good ClockAbsolute dicts.'''
    ClockAbsolute.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockAbsolute']['invalid'])
def test_ClockAbsolute_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockAbsolute dicts.'''
    with pytest.raises(ValidationError):
        ClockAbsolute.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVSpinlocks']['valid'])
def test_FeaturesHyperVSpinlocks_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVSpinlocks dicts.'''
    FeaturesHyperVSpinlocks.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVSpinlocks']['invalid'])
def test_FeaturesHyperVSpinlocks_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVSpinlocks dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVSpinlocks.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVSTimer']['valid'])
def test_FeaturesHyperVSTimer_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVSTimer dicts.'''
    FeaturesHyperVSTimer.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVSTimer']['invalid'])
def test_FeaturesHyperVSTimer_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVSTimer dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVSTimer.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVVendorID']['valid'])
def test_FeaturesHyperVVendorID_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVVendorID dicts.'''
    FeaturesHyperVVendorID.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVVendorID']['invalid'])
def test_FeaturesHyperVVendorID_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVVendorID dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVVendorID.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVInfo']['valid'])
def test_FeaturesHyperVInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesHyperVInfo dicts.'''
    FeaturesHyperVInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesHyperVInfo']['invalid'])
def test_FeaturesHyperVInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesHyperVInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesHyperVInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesKVMDirtyRing']['valid'])
def test_FeaturesKVMDirtyRing_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesKVMDirtyRing dicts.'''
    FeaturesKVMDirtyRing.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesKVMDirtyRing']['invalid'])
def test_FeaturesKVMDirtyRing_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesKVMDirtyRing dicts.'''
    with pytest.raises(ValidationError):
        FeaturesKVMDirtyRing.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesKVMInfo']['valid'])
def test_FeaturesKVMInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesKVMInfo dicts.'''
    FeaturesKVMInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesKVMInfo']['invalid'])
def test_FeaturesKVMInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesKVMInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesKVMInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesXenPassthrough']['valid'])
def test_FeaturesXenPassthrough_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesXenPassthrough dicts.'''
    FeaturesXenPassthrough.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesXenPassthrough']['invalid'])
def test_FeaturesXenPassthrough_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesXenPassthrough dicts.'''
    with pytest.raises(ValidationError):
        FeaturesXenPassthrough.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesXenInfo']['valid'])
def test_FeaturesXenInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesXenInfo dicts.'''
    FeaturesXenInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesXenInfo']['invalid'])
def test_FeaturesXenInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesXenInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesXenInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesTCGInfo']['valid'])
def test_FeaturesTCGInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesTCGInfo dicts.'''
    FeaturesTCGInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesTCGInfo']['invalid'])
def test_FeaturesTCGInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesTCGInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesTCGInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesAPICInfo']['valid'])
def test_FeaturesAPICInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesAPICInfo dicts.'''
    FeaturesAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesAPICInfo']['invalid'])
def test_FeaturesAPICInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesAPICInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesGICInfo']['valid'])
def test_FeaturesGICInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesGICInfo dicts.'''
    FeaturesGICInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesGICInfo']['invalid'])
def test_FeaturesGICInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesGICInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesGICInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesIOAPICInfo']['valid'])
def test_FeaturesIOAPICInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesIOAPICInfo dicts.'''
    FeaturesIOAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesIOAPICInfo']['invalid'])
def test_FeaturesIOAPICInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesIOAPICInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesIOAPICInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesSMMConfig']['valid'])
def test_FeaturesSMMConfig_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesSMMConfig dicts.'''
    FeaturesSMMConfig.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesSMMConfig']['invalid'])
def test_FeaturesSMMConfig_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesSMMConfig dicts.'''
    with pytest.raises(ValidationError):
        FeaturesSMMConfig.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesCapabilities']['valid'])
def test_FeaturesCapabilities_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesCapabilities dicts.'''
    FeaturesCapabilities.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesCapabilities']['invalid'])
def test_FeaturesCapabilities_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesCapabilities dicts.'''
    with pytest.raises(ValidationError):
        FeaturesCapabilities.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesInfo']['valid'])
def test_FeaturesInfo_valid(d: dict) -> None:
    '''Check validation of known-good FeaturesInfo dicts.'''
    FeaturesInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FeaturesInfo']['invalid'])
def test_FeaturesInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FeaturesInfo dicts.'''
    with pytest.raises(ValidationError):
        FeaturesInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ControllerDriverInfo']['valid'])
def test_ControllerDriverInfo_valid(d: dict) -> None:
    '''Check validation of known-good ControllerDriverInfo dicts.'''
    ControllerDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ControllerDriverInfo']['invalid'])
def test_ControllerDriverInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ControllerDriverInfo dicts.'''
    with pytest.raises(ValidationError):
        ControllerDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['SimpleController']['valid'])
def test_SimpleController_valid(d: dict) -> None:
    '''Check validation of known-good SimpleController dicts.'''
    SimpleController.model_validate(d)


@pytest.mark.parametrize('d', CASES['SimpleController']['invalid'])
def test_SimpleController_invalid(d: dict) -> None:
    '''Check validation of known-bad SimpleController dicts.'''
    with pytest.raises(ValidationError):
        SimpleController.model_validate(d)


@pytest.mark.parametrize('d', CASES['XenBusController']['valid'])
def test_XenBusController_valid(d: dict) -> None:
    '''Check validation of known-good XenBusController dicts.'''
    XenBusController.model_validate(d)


@pytest.mark.parametrize('d', CASES['XenBusController']['invalid'])
def test_XenBusController_invalid(d: dict) -> None:
    '''Check validation of known-bad XenBusController dicts.'''
    with pytest.raises(ValidationError):
        XenBusController.model_validate(d)


@pytest.mark.parametrize('d', CASES['IDEController']['valid'])
def test_IDEController_valid(d: dict) -> None:
    '''Check validation of known-good IDEController dicts.'''
    IDEController.model_validate(d)


@pytest.mark.parametrize('d', CASES['IDEController']['invalid'])
def test_IDEController_invalid(d: dict) -> None:
    '''Check validation of known-bad IDEController dicts.'''
    with pytest.raises(ValidationError):
        IDEController.model_validate(d)


@pytest.mark.parametrize('d', CASES['SCSIController']['valid'])
def test_SCSIController_valid(d: dict) -> None:
    '''Check validation of known-good SCSIController dicts.'''
    SCSIController.model_validate(d)


@pytest.mark.parametrize('d', CASES['SCSIController']['invalid'])
def test_SCSIController_invalid(d: dict) -> None:
    '''Check validation of known-bad SCSIController dicts.'''
    with pytest.raises(ValidationError):
        SCSIController.model_validate(d)


@pytest.mark.parametrize('d', CASES['USBController']['valid'])
def test_USBController_valid(d: dict) -> None:
    '''Check validation of known-good USBController dicts.'''
    USBController.model_validate(d)


@pytest.mark.parametrize('d', CASES['USBController']['invalid'])
def test_USBController_invalid(d: dict) -> None:
    '''Check validation of known-bad USBController dicts.'''
    with pytest.raises(ValidationError):
        USBController.model_validate(d)


@pytest.mark.parametrize('d', CASES['VirtIOSerialController']['valid'])
def test_VirtIOSerialController_valid(d: dict) -> None:
    '''Check validation of known-good VirtIOSerialController dicts.'''
    VirtIOSerialController.model_validate(d)


@pytest.mark.parametrize('d', CASES['VirtIOSerialController']['invalid'])
def test_VirtIOSerialController_invalid(d: dict) -> None:
    '''Check validation of known-bad VirtIOSerialController dicts.'''
    with pytest.raises(ValidationError):
        VirtIOSerialController.model_validate(d)


@pytest.mark.parametrize('d', CASES['DiskVolumeSrcInfo']['valid'])
def test_DiskVolumeSrcInfo_valid(d: dict) -> None:
    '''Check validation of known-good DiskVolumeSrcInfo dicts.'''
    DiskVolumeSrcInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['DiskVolumeSrcInfo']['invalid'])
def test_DiskVolumeSrcInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad DiskVolumeSrcInfo dicts.'''
    with pytest.raises(ValidationError):
        DiskVolumeSrcInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['DiskTargetInfo']['valid'])
def test_DiskTargetInfo_valid(d: dict) -> None:
    '''Check validation of known-good DiskTargetInfo dicts.'''
    DiskTargetInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['DiskTargetInfo']['invalid'])
def test_DiskTargetInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad DiskTargetInfo dicts.'''
    with pytest.raises(ValidationError):
        DiskTargetInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FileDisk']['valid'])
def test_FileDisk_valid(d: dict) -> None:
    '''Check validation of known-good FileDisk dicts.'''
    FileDisk.model_validate(d)


@pytest.mark.parametrize('d', CASES['FileDisk']['invalid'])
def test_FileDisk_invalid(d: dict) -> None:
    '''Check validation of known-bad FileDisk dicts.'''
    with pytest.raises(ValidationError):
        FileDisk.model_validate(d)


@pytest.mark.parametrize('d', CASES['BlockDisk']['valid'])
def test_BlockDisk_valid(d: dict) -> None:
    '''Check validation of known-good BlockDisk dicts.'''
    BlockDisk.model_validate(d)


@pytest.mark.parametrize('d', CASES['BlockDisk']['invalid'])
def test_BlockDisk_invalid(d: dict) -> None:
    '''Check validation of known-bad BlockDisk dicts.'''
    with pytest.raises(ValidationError):
        BlockDisk.model_validate(d)


@pytest.mark.parametrize('d', CASES['VolumeDisk']['valid'])
def test_VolumeDisk_valid(d: dict) -> None:
    '''Check validation of known-good VolumeDisk dicts.'''
    VolumeDisk.model_validate(d)


@pytest.mark.parametrize('d', CASES['VolumeDisk']['invalid'])
def test_VolumeDisk_invalid(d: dict) -> None:
    '''Check validation of known-bad VolumeDisk dicts.'''
    with pytest.raises(ValidationError):
        VolumeDisk.model_validate(d)


@pytest.mark.parametrize('d', CASES['FilesystemDriverInfo']['valid'])
def test_FilesystemDriverInfo_valid(d: dict) -> None:
    '''Check validation of known-good FilesystemDriverInfo dicts.'''
    FilesystemDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['FilesystemDriverInfo']['invalid'])
def test_FilesystemDriverInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad FilesystemDriverInfo dicts.'''
    with pytest.raises(ValidationError):
        FilesystemDriverInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['Filesystem']['valid'])
def test_Filesystem_valid(d: dict) -> None:
    '''Check validation of known-good Filesystem dicts.'''
    Filesystem.model_validate(d)


@pytest.mark.parametrize('d', CASES['Filesystem']['invalid'])
def test_Filesystem_invalid(d: dict) -> None:
    '''Check validation of known-bad Filesystem dicts.'''
    with pytest.raises(ValidationError):
        Filesystem.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkVPort']['valid'])
def test_NetworkVPort_valid(d: dict) -> None:
    '''Check validation of known-good NetworkVPort dicts.'''
    NetworkVPort.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkVPort']['invalid'])
def test_NetworkVPort_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkVPort dicts.'''
    with pytest.raises(ValidationError):
        NetworkVPort.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkIPv4Info']['valid'])
def test_NetworkIPv4Info_valid(d: dict) -> None:
    '''Check validation of known-good NetworkIPv4Info dicts.'''
    NetworkIPv4Info.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkIPv4Info']['invalid'])
def test_NetworkIPv4Info_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkIPv4Info dicts.'''
    with pytest.raises(ValidationError):
        NetworkIPv4Info.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkIPv6Info']['valid'])
def test_NetworkIPv6Info_valid(d: dict) -> None:
    '''Check validation of known-good NetworkIPv6Info dicts.'''
    NetworkIPv6Info.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkIPv6Info']['invalid'])
def test_NetworkIPv6Info_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkIPv6Info dicts.'''
    with pytest.raises(ValidationError):
        NetworkIPv6Info.model_validate(d)


@pytest.mark.parametrize('d', CASES['BridgeInterface']['valid'])
def test_BridgeInterface_valid(d: dict) -> None:
    '''Check validation of known-good BridgeInterface dicts.'''
    BridgeInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['BridgeInterface']['invalid'])
def test_BridgeInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad BridgeInterface dicts.'''
    with pytest.raises(ValidationError):
        BridgeInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['DirectInterface']['valid'])
def test_DirectInterface_valid(d: dict) -> None:
    '''Check validation of known-good DirectInterface dicts.'''
    DirectInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['DirectInterface']['invalid'])
def test_DirectInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad DirectInterface dicts.'''
    with pytest.raises(ValidationError):
        DirectInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['NullInterface']['valid'])
def test_NullInterface_valid(d: dict) -> None:
    '''Check validation of known-good NullInterface dicts.'''
    NullInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['NullInterface']['invalid'])
def test_NullInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad NullInterface dicts.'''
    with pytest.raises(ValidationError):
        NullInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['UserInterface']['valid'])
def test_UserInterface_valid(d: dict) -> None:
    '''Check validation of known-good UserInterface dicts.'''
    UserInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['UserInterface']['invalid'])
def test_UserInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad UserInterface dicts.'''
    with pytest.raises(ValidationError):
        UserInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['VirtualInterface']['valid'])
def test_VirtualInterface_valid(d: dict) -> None:
    '''Check validation of known-good VirtualInterface dicts.'''
    VirtualInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['VirtualInterface']['invalid'])
def test_VirtualInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad VirtualInterface dicts.'''
    with pytest.raises(ValidationError):
        VirtualInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['InputSource']['valid'])
def test_InputSource_valid(d: dict) -> None:
    '''Check validation of known-good InputSource dicts.'''
    InputSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['InputSource']['invalid'])
def test_InputSource_invalid(d: dict) -> None:
    '''Check validation of known-bad InputSource dicts.'''
    with pytest.raises(ValidationError):
        InputSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['SimpleInputDevice']['valid'])
def test_SimpleInputDevice_valid(d: dict) -> None:
    '''Check validation of known-good SimpleInputDevice dicts.'''
    SimpleInputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['SimpleInputDevice']['invalid'])
def test_SimpleInputDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad SimpleInputDevice dicts.'''
    with pytest.raises(ValidationError):
        SimpleInputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['PassthroughInputDevice']['valid'])
def test_PassthroughInputDevice_valid(d: dict) -> None:
    '''Check validation of known-good PassthroughInputDevice dicts.'''
    PassthroughInputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['PassthroughInputDevice']['invalid'])
def test_PassthroughInputDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad PassthroughInputDevice dicts.'''
    with pytest.raises(ValidationError):
        PassthroughInputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['EvdevInputDevice']['valid'])
def test_EvdevInputDevice_valid(d: dict) -> None:
    '''Check validation of known-good EvdevInputDevice dicts.'''
    EvdevInputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['EvdevInputDevice']['invalid'])
def test_EvdevInputDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad EvdevInputDevice dicts.'''
    with pytest.raises(ValidationError):
        EvdevInputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['NullGraphicsListener']['valid'])
def test_NullGraphicsListener_valid(d: dict) -> None:
    '''Check validation of known-good NullGraphicsListener dicts.'''
    NullGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['NullGraphicsListener']['invalid'])
def test_NullGraphicsListener_invalid(d: dict) -> None:
    '''Check validation of known-bad NullGraphicsListener dicts.'''
    with pytest.raises(ValidationError):
        NullGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['AddressGraphicsListener']['valid'])
def test_AddressGraphicsListener_valid(d: dict) -> None:
    '''Check validation of known-good AddressGraphicsListener dicts.'''
    AddressGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['AddressGraphicsListener']['invalid'])
def test_AddressGraphicsListener_invalid(d: dict) -> None:
    '''Check validation of known-bad AddressGraphicsListener dicts.'''
    with pytest.raises(ValidationError):
        AddressGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkGraphicsListener']['valid'])
def test_NetworkGraphicsListener_valid(d: dict) -> None:
    '''Check validation of known-good NetworkGraphicsListener dicts.'''
    NetworkGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkGraphicsListener']['invalid'])
def test_NetworkGraphicsListener_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkGraphicsListener dicts.'''
    with pytest.raises(ValidationError):
        NetworkGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['SocketGraphicsListener']['valid'])
def test_SocketGraphicsListener_valid(d: dict) -> None:
    '''Check validation of known-good SocketGraphicsListener dicts.'''
    SocketGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['SocketGraphicsListener']['invalid'])
def test_SocketGraphicsListener_invalid(d: dict) -> None:
    '''Check validation of known-bad SocketGraphicsListener dicts.'''
    with pytest.raises(ValidationError):
        SocketGraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['VNCGraphics']['valid'])
def test_VNCGraphics_valid(d: dict) -> None:
    '''Check validation of known-good VNCGraphics dicts.'''
    VNCGraphics.model_validate(d)


@pytest.mark.parametrize('d', CASES['VNCGraphics']['invalid'])
def test_VNCGraphics_invalid(d: dict) -> None:
    '''Check validation of known-bad VNCGraphics dicts.'''
    with pytest.raises(ValidationError):
        VNCGraphics.model_validate(d)


@pytest.mark.parametrize('d', CASES['SPICEGraphics']['valid'])
def test_SPICEGraphics_valid(d: dict) -> None:
    '''Check validation of known-good SPICEGraphics dicts.'''
    SPICEGraphics.model_validate(d)


@pytest.mark.parametrize('d', CASES['SPICEGraphics']['invalid'])
def test_SPICEGraphics_invalid(d: dict) -> None:
    '''Check validation of known-bad SPICEGraphics dicts.'''
    with pytest.raises(ValidationError):
        SPICEGraphics.model_validate(d)


@pytest.mark.parametrize('d', CASES['RDPGraphics']['valid'])
def test_RDPGraphics_valid(d: dict) -> None:
    '''Check validation of known-good RDPGraphics dicts.'''
    RDPGraphics.model_validate(d)


@pytest.mark.parametrize('d', CASES['RDPGraphics']['invalid'])
def test_RDPGraphics_invalid(d: dict) -> None:
    '''Check validation of known-bad RDPGraphics dicts.'''
    with pytest.raises(ValidationError):
        RDPGraphics.model_validate(d)


@pytest.mark.parametrize('d', CASES['VideoDevice']['valid'])
def test_VideoDevice_valid(d: dict) -> None:
    '''Check validation of known-good VideoDevice dicts.'''
    VideoDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['VideoDevice']['invalid'])
def test_VideoDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad VideoDevice dicts.'''
    with pytest.raises(ValidationError):
        VideoDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevSimpleSource']['valid'])
def test_CharDevSimpleSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevSimpleSource dicts.'''
    CharDevSimpleSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevSimpleSource']['invalid'])
def test_CharDevSimpleSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevSimpleSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevSimpleSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevPathSource']['valid'])
def test_CharDevPathSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevPathSource dicts.'''
    CharDevPathSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevPathSource']['invalid'])
def test_CharDevPathSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevPathSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevPathSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevPTYSource']['valid'])
def test_CharDevPTYSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevPTYSource dicts.'''
    CharDevPTYSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevPTYSource']['invalid'])
def test_CharDevPTYSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevPTYSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevPTYSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevSocketSource']['valid'])
def test_CharDevSocketSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevSocketSource dicts.'''
    CharDevSocketSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevSocketSource']['invalid'])
def test_CharDevSocketSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevSocketSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevSocketSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevTCPSource']['valid'])
def test_CharDevTCPSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevTCPSource dicts.'''
    CharDevTCPSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevTCPSource']['invalid'])
def test_CharDevTCPSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevTCPSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevTCPSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevChannelSource']['valid'])
def test_CharDevChannelSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevChannelSource dicts.'''
    CharDevChannelSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevChannelSource']['invalid'])
def test_CharDevChannelSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevChannelSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevChannelSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['ParallelDevTarget']['valid'])
def test_ParallelDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good ParallelDevTarget dicts.'''
    ParallelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['ParallelDevTarget']['invalid'])
def test_ParallelDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad ParallelDevTarget dicts.'''
    with pytest.raises(ValidationError):
        ParallelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['SerialDevTarget']['valid'])
def test_SerialDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good SerialDevTarget dicts.'''
    SerialDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['SerialDevTarget']['invalid'])
def test_SerialDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad SerialDevTarget dicts.'''
    with pytest.raises(ValidationError):
        SerialDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['ConsoleDevTarget']['valid'])
def test_ConsoleDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good ConsoleDevTarget dicts.'''
    ConsoleDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['ConsoleDevTarget']['invalid'])
def test_ConsoleDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad ConsoleDevTarget dicts.'''
    with pytest.raises(ValidationError):
        ConsoleDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetChannelDevTarget']['valid'])
def test_NetChannelDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good NetChannelDevTarget dicts.'''
    NetChannelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetChannelDevTarget']['invalid'])
def test_NetChannelDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad NetChannelDevTarget dicts.'''
    with pytest.raises(ValidationError):
        NetChannelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['VirtIOChannelDevTarget']['valid'])
def test_VirtIOChannelDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good VirtIOChannelDevTarget dicts.'''
    VirtIOChannelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['VirtIOChannelDevTarget']['invalid'])
def test_VirtIOChannelDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad VirtIOChannelDevTarget dicts.'''
    with pytest.raises(ValidationError):
        VirtIOChannelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['XenChannelDevTarget']['valid'])
def test_XenChannelDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good XenChannelDevTarget dicts.'''
    XenChannelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['XenChannelDevTarget']['invalid'])
def test_XenChannelDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad XenChannelDevTarget dicts.'''
    with pytest.raises(ValidationError):
        XenChannelDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevLog']['valid'])
def test_CharDevLog_valid(d: dict) -> None:
    '''Check validation of known-good CharDevLog dicts.'''
    CharDevLog.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevLog']['invalid'])
def test_CharDevLog_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevLog dicts.'''
    with pytest.raises(ValidationError):
        CharDevLog.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharacterDevice']['valid'])
def test_CharacterDevice_valid(d: dict) -> None:
    '''Check validation of known-good CharacterDevice dicts.'''
    CharacterDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharacterDevice']['invalid'])
def test_CharacterDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad CharacterDevice dicts.'''
    with pytest.raises(ValidationError):
        CharacterDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['WatchdogDevice']['valid'])
def test_WatchdogDevice_valid(d: dict) -> None:
    '''Check validation of known-good WatchdogDevice dicts.'''
    WatchdogDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['WatchdogDevice']['invalid'])
def test_WatchdogDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad WatchdogDevice dicts.'''
    with pytest.raises(ValidationError):
        WatchdogDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGBuiltinBackend']['valid'])
def test_RNGBuiltinBackend_valid(d: dict) -> None:
    '''Check validation of known-good RNGBuiltinBackend dicts.'''
    RNGBuiltinBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGBuiltinBackend']['invalid'])
def test_RNGBuiltinBackend_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGBuiltinBackend dicts.'''
    with pytest.raises(ValidationError):
        RNGBuiltinBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGRandomBackend']['valid'])
def test_RNGRandomBackend_valid(d: dict) -> None:
    '''Check validation of known-good RNGRandomBackend dicts.'''
    RNGRandomBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGRandomBackend']['invalid'])
def test_RNGRandomBackend_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGRandomBackend dicts.'''
    with pytest.raises(ValidationError):
        RNGRandomBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGEGDSocketBackend']['valid'])
def test_RNGEGDSocketBackend_valid(d: dict) -> None:
    '''Check validation of known-good RNGEGDSocketBackend dicts.'''
    RNGEGDSocketBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGEGDSocketBackend']['invalid'])
def test_RNGEGDSocketBackend_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGEGDSocketBackend dicts.'''
    with pytest.raises(ValidationError):
        RNGEGDSocketBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGEGDTCPBackend']['valid'])
def test_RNGEGDTCPBackend_valid(d: dict) -> None:
    '''Check validation of known-good RNGEGDTCPBackend dicts.'''
    RNGEGDTCPBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGEGDTCPBackend']['invalid'])
def test_RNGEGDTCPBackend_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGEGDTCPBackend dicts.'''
    with pytest.raises(ValidationError):
        RNGEGDTCPBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGDevice']['valid'])
def test_RNGDevice_valid(d: dict) -> None:
    '''Check validation of known-good RNGDevice dicts.'''
    RNGDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGDevice']['invalid'])
def test_RNGDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGDevice dicts.'''
    with pytest.raises(ValidationError):
        RNGDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['PassthroughTPM']['valid'])
def test_PassthroughTPM_valid(d: dict) -> None:
    '''Check validation of known-good PassthroughTPM dicts.'''
    PassthroughTPM.model_validate(d)


@pytest.mark.parametrize('d', CASES['PassthroughTPM']['invalid'])
def test_PassthroughTPM_invalid(d: dict) -> None:
    '''Check validation of known-bad PassthroughTPM dicts.'''
    with pytest.raises(ValidationError):
        PassthroughTPM.model_validate(d)


@pytest.mark.parametrize('d', CASES['EmulatedTPM']['valid'])
def test_EmulatedTPM_valid(d: dict) -> None:
    '''Check validation of known-good EmulatedTPM dicts.'''
    EmulatedTPM.model_validate(d)


@pytest.mark.parametrize('d', CASES['EmulatedTPM']['invalid'])
def test_EmulatedTPM_invalid(d: dict) -> None:
    '''Check validation of known-bad EmulatedTPM dicts.'''
    with pytest.raises(ValidationError):
        EmulatedTPM.model_validate(d)


@pytest.mark.parametrize('d', CASES['SimpleDevice']['valid'])
def test_SimpleDevice_valid(d: dict) -> None:
    '''Check validation of known-good SimpleDevice dicts.'''
    SimpleDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['SimpleDevice']['invalid'])
def test_SimpleDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad SimpleDevice dicts.'''
    with pytest.raises(ValidationError):
        SimpleDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['Devices']['valid'])
def test_Devices_valid(d: dict) -> None:
    '''Check validation of known-good Devices dicts.'''
    Devices.model_validate(d)


@pytest.mark.parametrize('d', CASES['Devices']['invalid'])
def test_Devices_invalid(d: dict) -> None:
    '''Check validation of known-bad Devices dicts.'''
    with pytest.raises(ValidationError):
        Devices.model_validate(d)


@pytest.mark.parametrize('d', CASES['DomainInfo']['valid'])
def test_DomainInfo_valid(d: dict) -> None:
    '''Check validation of known-good DomainInfo dicts.'''
    DomainInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['DomainInfo']['invalid'])
def test_DomainInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad DomainInfo dicts.'''
    with pytest.raises(ValidationError):
        DomainInfo.model_validate(d)
