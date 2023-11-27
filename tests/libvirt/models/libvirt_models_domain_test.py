# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.domain'''

from __future__ import annotations

import pytest

from psutil import cpu_count
from pydantic import ValidationError

from fvirt.libvirt.models.domain import (CharacterDevice, CharDevLog, CharDevSource, CharDevTarget, ClockInfo, ClockTimerInfo, ControllerDevice,
                                         ControllerDriverInfo, CPUInfo, CPUModelInfo, CPUTopology, DataRate, Devices, DiskDevice, DiskTargetInfo,
                                         DiskVolumeSrcInfo, DomainInfo, DriveAddress, FeaturesAPICInfo, FeaturesCapabilities, FeaturesGICInfo,
                                         FeaturesHyperVInfo, FeaturesHyperVSpinlocks, FeaturesHyperVSTimer, FeaturesHyperVVendorID, FeaturesInfo,
                                         FeaturesIOAPICInfo, FeaturesKVMDirtyRing, FeaturesKVMInfo, FeaturesTCGInfo, FeaturesXenInfo,
                                         FeaturesXenPassthrough, Filesystem, FilesystemDriverInfo, GraphicsDevice, GraphicsListener, InputDevice,
                                         InputSource, MemtuneInfo, NetworkInterface, NetworkIPInfo, NetworkVPort, OSContainerIDMapEntry,
                                         OSContainerIDMapInfo, OSFWLoaderInfo, OSFWNVRAMInfo, OSInfo, PCIAddress, RNGBackend, RNGDevice,
                                         SimpleDevice, TPMDevice, VideoDevice, WatchdogDevice)

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


def test_CPUTopology_infer_threads() -> None:
    '''Check that inferring threads for CPUTopology works.'''
    lcpus = cpu_count(logical=True)
    pcpus = cpu_count(logical=False)

    if lcpus is None or pcpus is None:
        pytest.skip('Unable to infer CPU topology on this system, skipping test.')

    model = CPUTopology(
        infer='threads',
    )

    assert model.threads == lcpus // pcpus


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


@pytest.mark.parametrize('d', CASES['OSInfo']['valid'])
def test_OSInfo_valid(d: dict) -> None:
    '''Check validation of known-good OSInfo dicts.'''
    OSInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['OSInfo']['invalid'])
def test_OSInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad OSInfo dicts.'''
    with pytest.raises(ValidationError):
        OSInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockTimerInfo']['valid'])
def test_ClockTimerInfo_valid(d: dict) -> None:
    '''Check validation of known-good ClockTimerInfo dicts.'''
    ClockTimerInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockTimerInfo']['invalid'])
def test_ClockTimerInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockTimerInfo dicts.'''
    with pytest.raises(ValidationError):
        ClockTimerInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockInfo']['valid'])
def test_ClockInfo_valid(d: dict) -> None:
    '''Check validation of known-good ClockInfo dicts.'''
    ClockInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['ClockInfo']['invalid'])
def test_ClockInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad ClockInfo dicts.'''
    with pytest.raises(ValidationError):
        ClockInfo.model_validate(d)


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


@pytest.mark.parametrize('d', CASES['ControllerDevice']['valid'])
def test_ControllerDevice_valid(d: dict) -> None:
    '''Check validation of known-good ControllerDevice dicts.'''
    ControllerDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['ControllerDevice']['invalid'])
def test_ControllerDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad ControllerDevice dicts.'''
    with pytest.raises(ValidationError):
        ControllerDevice.model_validate(d)


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


@pytest.mark.parametrize('d', CASES['DiskDevice']['valid'])
def test_DiskDevice_valid(d: dict) -> None:
    '''Check validation of known-good DiskDevice dicts.'''
    DiskDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['DiskDevice']['invalid'])
def test_DiskDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad DiskDevice dicts.'''
    with pytest.raises(ValidationError):
        DiskDevice.model_validate(d)


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


@pytest.mark.parametrize('d', CASES['NetworkIPInfo']['valid'])
def test_NetworkIPInfo_valid(d: dict) -> None:
    '''Check validation of known-good NetworkIPInfo dicts.'''
    NetworkIPInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkIPInfo']['invalid'])
def test_NetworkIPInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkIPInfo dicts.'''
    with pytest.raises(ValidationError):
        NetworkIPInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkInterface']['valid'])
def test_NetworkInterface_valid(d: dict) -> None:
    '''Check validation of known-good NetworkInterface dicts.'''
    NetworkInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['NetworkInterface']['invalid'])
def test_NetworkInterface_invalid(d: dict) -> None:
    '''Check validation of known-bad NetworkInterface dicts.'''
    with pytest.raises(ValidationError):
        NetworkInterface.model_validate(d)


@pytest.mark.parametrize('d', CASES['InputSource']['valid'])
def test_InputSource_valid(d: dict) -> None:
    '''Check validation of known-good InputSource dicts.'''
    InputSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['InputSource']['invalid'])
def test_InputSource_invalid(d: dict) -> None:
    '''Check validation of known-bad InputSource dicts.'''
    with pytest.raises(ValidationError):
        InputSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['InputDevice']['valid'])
def test_InputDevice_valid(d: dict) -> None:
    '''Check validation of known-good InputDevice dicts.'''
    InputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['InputDevice']['invalid'])
def test_InputDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad InputDevice dicts.'''
    with pytest.raises(ValidationError):
        InputDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['GraphicsListener']['valid'])
def test_GraphicsListener_valid(d: dict) -> None:
    '''Check validation of known-good GraphicsListener dicts.'''
    GraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['GraphicsListener']['invalid'])
def test_GraphicsListener_invalid(d: dict) -> None:
    '''Check validation of known-bad GraphicsListener dicts.'''
    with pytest.raises(ValidationError):
        GraphicsListener.model_validate(d)


@pytest.mark.parametrize('d', CASES['GraphicsDevice']['valid'])
def test_GraphicsDevice_valid(d: dict) -> None:
    '''Check validation of known-good GraphicsDevice dicts.'''
    GraphicsDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['GraphicsDevice']['invalid'])
def test_GraphicsDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad GraphicsDevice dicts.'''
    with pytest.raises(ValidationError):
        GraphicsDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['VideoDevice']['valid'])
def test_VideoDevice_valid(d: dict) -> None:
    '''Check validation of known-good VideoDevice dicts.'''
    VideoDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['VideoDevice']['invalid'])
def test_VideoDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad VideoDevice dicts.'''
    with pytest.raises(ValidationError):
        VideoDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevSource']['valid'])
def test_CharDevSource_valid(d: dict) -> None:
    '''Check validation of known-good CharDevSource dicts.'''
    CharDevSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevSource']['invalid'])
def test_CharDevSource_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevSource dicts.'''
    with pytest.raises(ValidationError):
        CharDevSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevTarget']['valid'])
def test_CharDevTarget_valid(d: dict) -> None:
    '''Check validation of known-good CharDevTarget dicts.'''
    CharDevTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['CharDevTarget']['invalid'])
def test_CharDevTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad CharDevTarget dicts.'''
    with pytest.raises(ValidationError):
        CharDevTarget.model_validate(d)


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


@pytest.mark.parametrize('d', CASES['RNGBackend']['valid'])
def test_RNGBackend_valid(d: dict) -> None:
    '''Check validation of known-good RNGBackend dicts.'''
    RNGBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGBackend']['invalid'])
def test_RNGBackend_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGBackend dicts.'''
    with pytest.raises(ValidationError):
        RNGBackend.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGDevice']['valid'])
def test_RNGDevice_valid(d: dict) -> None:
    '''Check validation of known-good RNGDevice dicts.'''
    RNGDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['RNGDevice']['invalid'])
def test_RNGDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad RNGDevice dicts.'''
    with pytest.raises(ValidationError):
        RNGDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['TPMDevice']['valid'])
def test_TPMDevice_valid(d: dict) -> None:
    '''Check validation of known-good TPMDevice dicts.'''
    TPMDevice.model_validate(d)


@pytest.mark.parametrize('d', CASES['TPMDevice']['invalid'])
def test_TPMDevice_invalid(d: dict) -> None:
    '''Check validation of known-bad TPMDevice dicts.'''
    with pytest.raises(ValidationError):
        TPMDevice.model_validate(d)


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
