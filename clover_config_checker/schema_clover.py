"""Clover r515x config.plist schema.

Field inventory mirrors the official CloverPackage/CloverV2/EFI/CLOVER/
config-sample.plist (CloverHackyColor/CloverBootloader master), plus
long-standing settings documented in the Clover wiki.

Conventions handled by the checker:
  * '#'-prefixed keys  -> Clover comment keys, always allowed.
  * '?'-suffixed keys  -> sample-file documentation markers (optional
    entries). Clover does NOT apply them; the checker suggests removing '?'.
  * 'SMBIOS_<os>'      -> per-OS SMBIOS presets reuse the SMBIOS schema.
"""

from .schema import (
    Field, B, S, DATA, HEXNUM, HEXSTR, UUID, NUM, DICT, FREE, ARR, FLEX,
    T_ANY, T_ARR, T_BOOL, T_DATA, T_DICT, T_INT, T_REAL, T_STR,
    patch_item,
)

# ---------------------------------------------------------------- ACPI ----

_DSDT_FIXES = DICT('Fixes', {
    'AddDTGP': B('AddDTGP'), 'AddHDMI': B('AddHDMI'), 'AddIMEI': B('AddIMEI'),
    'AddMCHC': B('AddMCHC'), 'AddPNLF': B('AddPNLF'),
    'DeleteUnused': B('DeleteUnused'), 'FakeLPC': B('FakeLPC'),
    'FixACST': B('FixACST'), 'FixADP1': B('FixADP1'),
    'FixAirport': B('FixAirport'), 'FixDarwin': B('FixDarwin'),
    'FixDarwin7': B('FixDarwin7'), 'FixDisplay': B('FixDisplay'),
    'FixFirewire': B('FixFirewire'), 'FixHDA': B('FixHDA'),
    'FixHPET': B('FixHPET'), 'FixIDE': B('FixIDE'), 'FixIPIC': B('FixIPIC'),
    'FixIntelGfx': B('FixIntelGfx'), 'FixLAN': B('FixLAN'),
    'FixMutex': B('FixMutex'), 'FixRTC': B('FixRTC'),
    'FixRegions': B('FixRegions'), 'FixS3D': B('FixS3D'),
    'FixSATA': B('FixSATA'), 'FixSBUS': B('FixSBUS'),
    'FixShutdown': B('FixShutdown'), 'FixTMR': B('FixTMR'),
    'FixUSB': B('FixUSB'), 'FixWAK': B('FixWAK'),
})

_ACPI = DICT('ACPI', {
    'AutoMerge': B('AutoMerge'),
    'DSDT': DICT('DSDT', {
        'Debug': B('Debug'),
        'Fixes': _DSDT_FIXES,
        'Name': S('Name'),
        'PNLF_UID': HEXSTR('PNLF_UID'),
        'Patches': ARR('Patches', patch_item('Patches[]'), note='binary DSDT patches'),
        'ReuseFFFF': B('ReuseFFFF'),
        'Rtc8Allowed': B('Rtc8Allowed'),
        'SuspendOverride': B('SuspendOverride'),
    }),
    'DisableASPM': B('DisableASPM'),
    'DisabledAML': ARR('DisabledAML', S('DisabledAML[]'),
                       note='list of SSDT/DSDT file names to disable'),
    'DropTables': ARR('DropTables', DICT('DropTables[]', {
        'Signature': S('Signature'),
        'TableId': S('TableId'),
        'Length': NUM('Length', vmin=0),
        'MaskLength': NUM('MaskLength', vmin=0),
        'DropForAllOS': B('DropForAllOS'),
    })),
    'FixHeaders': B('FixHeaders'),
    'FixMCFG': B('FixMCFG'),
    'HaltEnabler': B('HaltEnabler'),
    'PatchAPIC': B('PatchAPIC'),
    'RenameDevices': ARR('RenameDevices', FREE('RenameDevices[]'),
                         note='dict of device path -> new name'),
    'ResetAddress': HEXNUM('ResetAddress'),
    'ResetBus': NUM('ResetBus'),
    'ResetValue': HEXNUM('ResetValue'),
    'SSDT': DICT('SSDT', {
        'C3Latency': HEXNUM('C3Latency'),
        'DoubleFirstState': B('DoubleFirstState'),
        'DropOem': B('DropOem'),
        'EnableC2': B('EnableC2'), 'EnableC4': B('EnableC4'),
        'EnableC6': B('EnableC6'), 'EnableC7': B('EnableC7'),
        'EnableISS': B('EnableISS'),
        'Generate': DICT('Generate', {
            'APLF': B('APLF'), 'APSN': B('APSN'),
            'CStates': B('CStates'), 'PStates': B('PStates'),
            'PluginType': B('PluginType'),
        }),
        'MaxMultiplier': NUM('MaxMultiplier', vmin=1),
        'MinMultiplier': NUM('MinMultiplier', vmin=1),
        'NoDynamicExtract': B('NoDynamicExtract'),
        'NoInline': B('NoInline'),
        'NoOemTableId': B('NoOemTableId'),
        'PLimitDict': NUM('PLimitDict'),
        'UnderVoltStep': NUM('UnderVoltStep'),
        'UseSystemIO': B('UseSystemIO'),
    }),
    'SortedOrder': ARR('SortedOrder', S('SortedOrder[]')),
    'smartUPS': B('smartUPS'),
})

# ---------------------------------------------------------------- Boot ----

_BOOT = DICT('Boot', {
    'Arguments': S('Arguments', note='boot-args string, e.g. -v keepsyms=1'),
    'CustomLogo': FLEX('CustomLogo', (T_BOOL, T_STR, T_DATA),
                       note='false/true, image path or image data'),
    'Debug': B('Debug'),
    'DefaultLoader': S('DefaultLoader'),
    'DefaultVolume': S('DefaultVolume'),
    'DisableCloverHotkeys': B('DisableCloverHotkeys'),
    'Fast': B('Fast'),
    'Legacy': FLEX('Legacy', (T_STR, T_BOOL), enum=('PBR', 'BIOS'),
                   enum_warn=True, note='PBR (default) or BIOS'),
    'LegacyBiosDefaultEntry': NUM('LegacyBiosDefaultEntry', vmin=0),
    'NeverDoRecovery': B('NeverDoRecovery'),
    'NeverHibernate': B('NeverHibernate'),
    'NoEarlyProgress': B('NoEarlyProgress'),
    'RtcHibernateAware': B('RtcHibernateAware'),
    'Secure': NUM('Secure', vmin=0, vmax=3),
    'SignatureFixup': B('SignatureFixup'),
    'SkipHibernateTimeout': B('SkipHibernateTimeout'),
    'StrictHibernate': B('StrictHibernate'),
    'Timeout': NUM('Timeout', vmin=0,
                   note='seconds before default volume boots; 0 = immediate'),
    'XMPDetection': FLEX('XMPDetection', (T_INT, T_STR), vmin=-1, vmax=2,
                         note='-1..2, or Yes/No'),
})

# --------------------------------------------------------- BootGraphics ----

_BOOTGRAPHICS = DICT('BootGraphics', {
    'DefaultBackgroundColor': HEXNUM('DefaultBackgroundColor'),
    'EFILoginHiDPI': NUM('EFILoginHiDPI', vmin=0, vmax=2),
    'UIScale': NUM('UIScale', vmin=1, vmax=2),
})

# ------------------------------------------------------------------ CPU ----

_CPU = DICT('CPU', {
    'ArtificialFreq': NUM('ArtificialFreq'),
    'BusSpeedkHz': NUM('BusSpeedkHz'),
    'FrequencyMHz': NUM('FrequencyMHz'),
    'HWPEnable': B('HWPEnable'),
    'HWPValue': HEXSTR('HWPValue'),
    'QPI': NUM('QPI'),
    'SavingMode': NUM('SavingMode'),
    'TDP': NUM('TDP'),
    'TurboDisable': B('TurboDisable'),
    'Type': HEXSTR('Type'),
    'UseARTFrequency': B('UseARTFrequency'),
    'UseArtificialFreq': B('UseArtificialFreq'),
})

# ------------------------------------------------------------- Devices ----

_DEVICES = DICT('Devices', {
    'AddProperties': ARR('AddProperties', DICT('AddProperties[]', {
        'Device': S('Device'),
        'Key': S('Key'),
        'Value': Field('Value', (T_ANY,)),
        'Disabled': B('Disabled'),
    })),
    'Arpt': NUM('Arpt'),
    'Audio': DICT('Audio', {
        'AFGLowPowerState': B('AFGLowPowerState'),
        'Inject': FLEX('Inject', (T_INT, T_STR, T_BOOL),
                       note='layout-id number, "Detect" or false'),
        'ResetHDA': B('ResetHDA'),
    }),
    'DisableFunctions': HEXSTR('DisableFunctions'),
    'FakeID': DICT('FakeID', {
        'ATI': HEXSTR('ATI'), 'IMEI': HEXSTR('IMEI'),
        'IntelGFX': HEXSTR('IntelGFX'), 'LAN': HEXSTR('LAN'),
        'NVidia': HEXSTR('NVidia'), 'SATA': HEXSTR('SATA'),
        'WIFI': HEXSTR('WIFI'), 'XHCI': HEXSTR('XHCI'),
        'WMI': B('WMI'),
    }),
    'ForceHPET': B('ForceHPET'),
    'HDMIInjection': B('HDMIInjection'),
    'IntelMaxValue': HEXSTR('IntelMaxValue'),
    'LAN': NUM('LAN'),
    'LANInjection': B('LANInjection'),
    'NoDefaultProperties': B('NoDefaultProperties'),
    'Properties': FREE('Properties',
                       note='dict of PciRoot(0x..)/Pci(..) -> device properties'),
    'SetIntelBacklight': B('SetIntelBacklight'),
    'SetIntelMaxBacklight': B('SetIntelMaxBacklight'),
    'USB': DICT('USB', {
        'AddClockID': B('AddClockID'),
        'FixOwnership': B('FixOwnership'),
        'HighCurrent': B('HighCurrent'),
        'Inject': B('Inject'),
        'InjectClockID': B('InjectClockID'),
    }),
    'UseIntelHDMI': B('UseIntelHDMI'),
})

# ----------------------------------------------------------------- GUI ----

_GUI_ENTRY_FIELDS = {
    'AddArguments': S('AddArguments',
                      note='appended to the default boot arguments'),
    'AddSubMenu': B('AddSubMenu'),
    'Arguments': S('Arguments'),
    'Comment': S('Comment'),
    'Disabled': B('Disabled'),
    'FullTitle': S('FullTitle'),
    'Hidden': B('Hidden'),
    'Hotkey': S('Hotkey', note='single character'),
    'Ignore': B('Ignore'),
    'Image': S('Image', note='custom icon name for the entry'),
    'ImagePath': S('ImagePath'),
    'InjectKexts': FLEX('InjectKexts', (T_BOOL, T_INT, T_STR),
                        enum=('Yes', 'No', 'Detect', 'yes', 'no', 'detect'),
                        enum_warn=True),
    'NoCaches': B('NoCaches'),
    'Path': S('Path'),
    'Subtitle': S('Subtitle'),
    'Title': S('Title'),
    'Type': S('Type', enum=('OSX', 'OSXInstaller', 'OSXRecovery', 'Windows',
                            'WindowsInstaller', 'Linux', 'LinuxKernel', 'Other'),
              enum_warn=True),
    'Volume': S('Volume'),
    'VolumeType': FLEX('VolumeType', (T_STR, T_ARR),
                       enum=('Internal', 'External', 'Optical', 'Firewire',
                             'USB'),
                       enum_warn=True),
}

_GUI_ENTRY = DICT('GUI/Custom/Entries[]', _GUI_ENTRY_FIELDS)
# Nested custom entries: SubEntries reuses the entry structure itself.
_GUI_ENTRY_FIELDS['SubEntries'] = ARR('SubEntries', _GUI_ENTRY)

_GUI_LEGACY = DICT('GUI/Custom/Legacy[]', {
    'Comment': S('Comment'),
    'Disabled': B('Disabled'),
    'FullTitle': S('FullTitle'),
    'Hidden': B('Hidden'),
    'Hotkey': S('Hotkey'),
    'Title': S('Title'),
    'Type': S('Type', enum=('Windows', 'Linux', 'Other'), enum_warn=True),
    'Volume': S('Volume'),
    'VolumeType': FLEX('VolumeType', (T_STR, T_ARR),
                       enum=('Internal', 'External', 'Optical', 'Firewire',
                             'USB'),
                       enum_warn=True),
})

_GUI_TOOL = DICT('GUI/Custom/Tool[]', {
    'Arguments': S('Arguments'),
    'Comment': S('Comment'),
    'Disabled': B('Disabled'),
    'FullTitle': S('FullTitle'),
    'Hidden': B('Hidden'),
    'Hotkey': S('Hotkey'),
    'ImagePath': S('ImagePath'),
    'Path': S('Path'),
    'Title': S('Title'),
    'Volume': S('Volume'),
    'VolumeType': FLEX('VolumeType', (T_STR, T_ARR),
                       enum=('Internal', 'External', 'Optical', 'Firewire',
                             'USB'),
                       enum_warn=True),
})

_GUI = DICT('GUI', {
    'ConsoleMode': FLEX('ConsoleMode', (T_STR, T_INT)),
    'Custom': DICT('Custom', {
        'Entries': ARR('Entries', _GUI_ENTRY),
        'Legacy': ARR('Legacy', _GUI_LEGACY),
        'Tool': ARR('Tool', _GUI_TOOL),
    }),
    'CustomIcons': B('CustomIcons'),
    'EmbeddedThemeType': S('EmbeddedThemeType',
                           enum=('Daytime', 'Night', 'Light', 'Dark'),
                           enum_warn=True),
    'Hide': ARR('Hide', S('Hide[]'), note='volume names/UUIDs to hide'),
    'KbdMode': NUM('KbdMode', vmin=0, vmax=2),
    'KbdPrevLang': B('KbdPrevLang'),
    'Language': S('Language'),
    'Mouse': DICT('Mouse', {
        'CursorEnabled': B('CursorEnabled'),
        'DoubleClickTime': NUM('DoubleClickTime'),
        'DoubleClick': NUM('DoubleClick'),
        'Enabled': B('Enabled'),
        'Mirror': B('Mirror'),
        'Speed': NUM('Speed'),
    }),
    'PlayAsync': B('PlayAsync'),
    'ProvideConsoleGop': B('ProvideConsoleGop'),
    'Scan': FLEX('Scan', (T_DICT, T_BOOL), fields={
        'Enable': B('Enable'),
        'Entries': B('Entries'),
        'Kernel': S('Kernel'),
        'Legacy': FLEX('Legacy', (T_BOOL, T_STR),
                       enum=('NO', 'First', 'Last'), enum_warn=True),
        'Linux': B('Linux'),
        'Tool': B('Tool'),
    }),
    'ScreenResolution': S('ScreenResolution',
                          pattern=r'^\d+x\d+$', pattern_warn=True),
    'ShowOptimus': B('ShowOptimus'),
    'TextOnly': B('TextOnly'),
    'Theme': FLEX('Theme', (T_STR, T_DICT), fields={
        'BootcampStyle': B('BootcampStyle'),
        'CharWidth': NUM('CharWidth'),
        'Embedded': B('Embedded'),
        'Font': S('Font', enum=('Gray', 'White', 'Dark'), enum_warn=True),
        'Layout': S('Layout'),
        'Path': S('Path'),
        'Screensaver': NUM('Screensaver'),
        'SelectionColor': HEXSTR('SelectionColor'),
        'Type': S('Type'),
    }),
    'Timezone': NUM('Timezone', vmin=0, vmax=24),
})

# ------------------------------------------------------------ Graphics ----

_GRAPHICS = DICT('Graphics', {
    'display-cfg': Field('display-cfg', (T_STR,),
                         pattern=r'^(0[xX][0-9A-Fa-f]+|[0-9A-Fa-f]+)?$',
                         value_note='hex byte string, e.g. 03010300FFFF0001'),
    'DualLink': NUM('DualLink', vmin=0, vmax=1),
    'EDID': DICT('EDID', {
        'Custom': DATA('Custom'),
        'HorizontalSyncPulseWidth': HEXSTR('HorizontalSyncPulseWidth'),
        'Inject': B('Inject'),
        'ProductID': HEXSTR('ProductID'),
        'VendorID': HEXSTR('VendorID'),
        'VideoInputSignal': HEXSTR('VideoInputSignal'),
    }),
    'FBName': S('FBName'),
    'Inject': FLEX('Inject', (T_DICT, T_BOOL, T_STR), fields={
        'ATI': B('ATI'), 'Intel': B('Intel'), 'NVidia': B('NVidia'),
    }, note='preferred form is a dict of ATI/Intel/NVidia booleans'),
    'ig-platform-id': FLEX('ig-platform-id', (T_STR, T_INT),
                           note='hex string like 0x01620005'),
    'LoadVBios': B('LoadVBios'),
    'NVCAP': FLEX('NVCAP', (T_STR, T_DATA)),
    'NvidiaGeneric': B('NvidiaGeneric'),
    'NvidiaNoEFI': B('NvidiaNoEFI'),
    'NvidiaSingle': B('NvidiaSingle'),
    'PatchVBios': B('PatchVBios'),
    'PatchVBiosBytes': ARR('PatchVBiosBytes', DICT('PatchVBiosBytes[]', {
        'Find': Field('Find', (T_DATA,)),
        'Replace': Field('Replace', (T_DATA,)),
    })),
    'RadeonDeInit': B('RadeonDeInit'),
    'VRAM': NUM('VRAM', vmin=0),
    'VideoPorts': NUM('VideoPorts', vmin=0, vmax=6),
})

# ------------------------------------------------- KernelAndKextPatches ----

_KKP = DICT('KernelAndKextPatches', {
    'AppleIntelCPUPM': B('AppleIntelCPUPM'),
    'AppleRTC': B('AppleRTC'),
    'BootPatches': ARR('BootPatches', patch_item('BootPatches[]')),
    'Debug': B('Debug'),
    'DellSMBIOSPatch': B('DellSMBIOSPatch'),
    'EightApple': B('EightApple'),
    'FakeCPUID': HEXSTR('FakeCPUID'),
    'ForceKextsToLoad': ARR('ForceKextsToLoad', S('ForceKextsToLoad[]')),
    'KernelCpu': B('KernelCpu'),
    'KernelLapic': B('KernelLapic'),
    'KernelPm': B('KernelPm'),
    'KernelToPatch': ARR('KernelToPatch',
                         patch_item('KernelToPatch[]')),
    'KernelXCPM': B('KernelXCPM'),
    'KextsToBlock': ARR('KextsToBlock', DICT('KextsToBlock[]', {
        'Comment': S('Comment'),
        'Disabled': B('Disabled'),
        'MatchOS': S('MatchOS'),
        'Name': S('Name'),
    })),
    'KextsToPatch': ARR('KextsToPatch', patch_item(
        'KextsToPatch[]',
        {'InfoPlistPatch': B('InfoPlistPatch'),
         'Name': S('Name', note='kext bundle id or name'),
         'MatchKeyboardLanguage': S('MatchKeyboardLanguage'),
         'BundleVersion': S('BundleVersion'),
         'PseudoCPUID': S('PseudoCPUID')})),
    'PanicNoKextDump': B('PanicNoKextDump'),
})

# -------------------------------------------------------------- Quirks ----

_QUIRKS = DICT('Quirks', {
    'AppleXcpmExtraMsrs': B('AppleXcpmExtraMsrs'),
    'AppleXcpmForceBoost': B('AppleXcpmForceBoost'),
    'AutoModernCPUQuirks': B('AutoModernCPUQuirks'),
    'AvoidRuntimeDefrag': B('AvoidRuntimeDefrag'),
    'ClearTaskSwitchBit': B('ClearTaskSwitchBit'),
    'DevirtualiseMmio': B('DevirtualiseMmio'),
    'DisableIoMapper': B('DisableIoMapper'),
    'DisableIoMapperMapping': B('DisableIoMapperMapping'),
    'DisableLinkeditJettison': B('DisableLinkeditJettison'),
    'DisableSingleUser': B('DisableSingleUser'),
    'DisableVariableWrite': B('DisableVariableWrite'),
    'DiscardHibernateMap': B('DiscardHibernateMap'),
    'DummyPowerManagement': B('DummyPowerManagement'),
    'EnableSafeModeSlide': B('EnableSafeModeSlide'),
    'EnableWriteUnprotector': B('EnableWriteUnprotector'),
    'ExtendBTFeatureFlags': B('ExtendBTFeatureFlags'),
    'ExternalDiskIcons': B('ExternalDiskIcons'),
    'ForceAquantiaEthernet': B('ForceAquantiaEthernet'),
    'ForceExitBootServices': B('ForceExitBootServices'),
    'ForceOcWriteFlash': B('ForceOcWriteFlash'),
    'FuzzyMatch': B('FuzzyMatch'),
    'IncreasePciBarSize': B('IncreasePciBarSize'),
    'KernelCache': S('KernelCache', enum=('Auto', 'Cacheless', 'Mkext',
                                          'Prelinked'),
                     enum_warn=True),
    'MmioWhitelist': ARR('MmioWhitelist', DICT('MmioWhitelist[]', {
        'Address': NUM('Address'),
        'Comment': S('Comment'),
        'Enabled': B('Enabled'),
    })),
    'PowerTimeoutKernelPanic': B('PowerTimeoutKernelPanic'),
    'ProtectMemoryRegions': B('ProtectMemoryRegions'),
    'ProtectSecureBoot': B('ProtectSecureBoot'),
    'ProtectUefiServices': B('ProtectUefiServices'),
    'ProvideCurrentCpuInfo': B('ProvideCurrentCpuInfo'),
    'ProvideCustomSlide': B('ProvideCustomSlide'),
    'ProvideMaxSlide': NUM('ProvideMaxSlide', vmin=0, vmax=255),
    'RebuildAppleMemoryMap': B('RebuildAppleMemoryMap'),
    'ResizeAppleGpuBars': NUM('ResizeAppleGpuBars', vmin=-1, vmax=15),
    'ResizeGpuBars': NUM('ResizeGpuBars', vmin=-1, vmax=15),
    'SetupVirtualMap': B('SetupVirtualMap'),
    'SignalAppleOS': B('SignalAppleOS'),
    'SyncRuntimePermissions': B('SyncRuntimePermissions'),
    'ThirdPartyDrives': B('ThirdPartyDrives'),
    'TscSyncTimeout': NUM('TscSyncTimeout', vmin=0),
    'XhciPortLimit': B('XhciPortLimit'),
})

# ---------------------------------------------------------- RtVariables ----

_RT_VARIABLES = DICT('RtVariables', {
    'Block': ARR('Block', DICT('Block[]', {
        'Comment': S('Comment'),
        'Disabled': B('Disabled'),
        'Guid': S('Guid'),
        'Name': S('Name'),
    })),
    'BooterConfig': HEXNUM('BooterConfig', vmin=0),
    'CsrActiveConfig': HEXNUM('CsrActiveConfig', vmin=0),
    'HWTarget': S('HWTarget'),
    'MLB': S('MLB', note='Apple Board Serial: typically 17 characters'),
    'ROM': FLEX('ROM', (T_DATA, T_STR),
                enum=('UseMacAddr0', 'UseMacAddr1', 'UseMacAddr2',
                      'UseMacAddr3'),
                note='6-byte data, hex string, or UseMacAddr0..3'),
})

# --------------------------------------------------------------- SMBIOS ----

_SMBIOS = DICT('SMBIOS', {
    'BiosReleaseDate': S('BiosReleaseDate'),
    'BiosVendor': S('BiosVendor'),
    'BiosVersion': S('BiosVersion'),
    'Board-ID': S('Board-ID'),
    'BoardManufacturer': S('BoardManufacturer'),
    'BoardNumber': S('BoardNumber'),
    'BoardSerialNumber': S('BoardSerialNumber'),
    'BoardType': NUM('BoardType', vmin=0, vmax=255),
    'BoardVersion': S('BoardVersion'),
    'ChassisAssetTag': S('ChassisAssetTag'),
    'ChassisManufacturer': S('ChassisManufacturer'),
    'ChassisType': FLEX('ChassisType', (T_INT, T_STR), vmin=0, vmax=255),
    'ChassisSerialNumber': S('ChassisSerialNumber'),
    'ChassisVersion': S('ChassisVersion'),
    'EfiVersion': S('EfiVersion'),
    'ExtendedFirmwareFeatures': FLEX('ExtendedFirmwareFeatures',
                                     (T_STR, T_INT)),
    'ExtendedFirmwareFeaturesMask': FLEX('ExtendedFirmwareFeaturesMask',
                                         (T_STR, T_INT)),
    'FakeCPUID': HEXSTR('FakeCPUID'),
    'Family': S('Family'),
    'FirmwareFeatures': FLEX('FirmwareFeatures', (T_STR, T_INT)),
    'FirmwareFeaturesMask': FLEX('FirmwareFeaturesMask', (T_STR, T_INT)),
    'LocationInChassis': S('LocationInChassis'),
    'Manufacturer': S('Manufacturer'),
    'Memory': DICT('Memory', {
        'Channels': NUM('Channels', vmin=1, vmax=4),
        'Modules': ARR('Modules', DICT('Modules[]', {
            'Frequency': NUM('Frequency', vmin=0),
            'Part': S('Part'),
            'Serial': S('Serial'),
            'Size': NUM('Size', vmin=0),
            'Slot': NUM('Slot', vmin=0),
            'Type': S('Type', enum=('DDR', 'DDR2', 'DDR3', 'DDR4', 'DDR5',
                                    'LPDDR3', 'LPDDR4', 'LPDDR5'),
                      enum_warn=True),
            'Vendor': S('Vendor'),
        })),
        'SlotCount': NUM('SlotCount', vmin=1),
    }),
    'MemoryRank': NUM('MemoryRank'),
    'Mobile': B('Mobile'),
    'NoRomInfo': B('NoRomInfo'),
    'PlatformFeature': FLEX('PlatformFeature', (T_STR, T_INT)),
    'ProductName': S('ProductName'),
    'SerialNumber': S('SerialNumber'),
    'Slots': ARR('Slots', DICT('Slots[]', {
        'Device': S('Device'),
        'ID': NUM('ID'),
        'Name': S('Name'),
        'Type': NUM('Type'),
    })),
    'SmUUID': UUID('SmUUID'),
    'SmbiosVersion': HEXSTR('SmbiosVersion'),
    'Trust': B('Trust'),
    'Version': S('Version'),
})

# ---------------------------------------------------- SystemParameters ----

_SYSTEM_PARAMETERS = DICT('SystemParameters', {
    'BacklightLevel': FLEX('BacklightLevel', (T_STR, T_INT)),
    'CustomUUID': UUID('CustomUUID'),
    'InjectKexts': FLEX('InjectKexts', (T_BOOL, T_INT, T_STR),
                        enum=('Yes', 'No', 'Detect', 'yes', 'no', 'detect'),
                        enum_warn=True,
                        note='Yes/No/Detect (string), true/false or -1..2'),
    'InjectSystemID': B('InjectSystemID'),
    'NoCaches': B('NoCaches'),
    'NvramPrefsList': B('NvramPrefsList'),
    'NvidiaWeb': B('NvidiaWeb'),
})

# ----------------------------------------------------------------- root ----

ROOT_FIELDS = {
    'ACPI': _ACPI,
    'Boot': _BOOT,
    'BootGraphics': _BOOTGRAPHICS,
    'CPU': _CPU,
    'Devices': _DEVICES,
    'DisableDrivers': ARR('DisableDrivers', S('DisableDrivers[]')),
    'GUI': _GUI,
    'Graphics': _GRAPHICS,
    'KernelAndKextPatches': _KKP,
    'Quirks': _QUIRKS,
    'RtVariables': _RT_VARIABLES,
    'SMBIOS': _SMBIOS,
    'SystemParameters': _SYSTEM_PARAMETERS,
}

# ------------------------------------------------------------- extras -----

# Sections modern Clover expects to exist. The OpenCore quirks engine was
# integrated into Clover (r5123+); without a Quirks section recent Clover
# releases abort the boot ("Did not find config.plist/quirks. Fatal error").
REQUIRED_SECTIONS = {
    'Quirks': 'OpenCore-style quirks are integrated into Clover since '
              'r5123 and are vital for booting modern macOS -- copy the '
              'Quirks dict from the official config-sample.plist',
}

# Keys renamed or retired by newer Clover releases. Exact-match only; the
# message tells the user where the setting went.
DEPRECATED = {
    'ACPI/DSDT/FixDebug': 'legacy single switches were replaced by ACPI/DSDT/Fixes dict',
    'ACPI/DSDT/DropOEM_DSM': 'legacy option, replaced by ACPI/DSDT/Fixes and DisabledAML',
    'Boot/FastBoot': 'renamed to Boot/Fast',
    'Boot/Log': 'moved to Boot/Debug (boolean) in recent Clover',
    'Devices/AddProperties': 'replaced by Devices/Properties dict',
    'Devices/Audio/HDAInjection': 'renamed to Devices/Audio/Inject',
    'Devices/USB/InjectClockID': 'renamed to Devices/USB/AddClockID',
    'Graphics/IgPlatform': 'renamed to Graphics/ig-platform-id',
    'GUI/HideVolume': 'renamed to GUI/Hide',
    'KernelAndKextPatches/AtiConfig': 'legacy Clover option, no longer used by modern Clover',
    'KernelAndKextPatches/AtiConnectors': 'legacy Clover option, no longer used by modern Clover',
    'KernelAndKextPatches/BlockSkywalk': 'removed in Clover r5155 -- use the KernelAndKextPatches/KextsToBlock section to block com.apple.iokit.IOSkywalkFamily instead',
    'SMBIOS/BoardNumber': 'renamed to SMBIOS/Board-ID',
}


def is_smbios_preset(name: str) -> bool:
    """SMBIOS_capitan / SMBIOS_ventura ... -> per-OS SMBIOS presets."""
    return name.startswith('SMBIOS_')


def smbios_preset_schema() -> Field:
    return _SMBIOS
