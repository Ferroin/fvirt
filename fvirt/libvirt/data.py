# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared data used by other fvirt.libvirt modules.

   This is used to help avoid import loops and other undesirable dependency issues.'''

from __future__ import annotations

from typing import Final

FILE_VOLUME_FORMATS: Final = {
    'raw': 'Raw disk image',
    'bochs': 'Bochs disk image',
    'cloop': 'Compressed loop disk image',
    'dmg': 'macOS disk image',
    'iso': 'ISO 9660 disk image',
    'qcow': 'QEMU copy on write v1 disk image',
    'qcow2': 'QEMU copy on write v2 disk image',
    'qed': 'QEMU enhanced disk image',
    'vmdk': 'VMWare disk image',
    'vpc': 'VirtualPC disk image',
}

POOL_TYPE_INFO: Final = {
    'dir': {
        'type': 'dir',
        'name': 'Directory pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
            'source': dict(),
            'features': {
                'cow': True,
            },
        },
        'volume': {
            'formats': FILE_VOLUME_FORMATS,
            'target': {
                'nocow': True,
            },
        },
    },
    'fs': {
        'type': 'fs',
        'name': 'Filesystem pool',
        'pool': {
            'formats': {
                'auto': 'Automatically determine format',
                'ext2': 'Linux ext2',
                'ext3': 'Linux ext3',
                'ext4': 'Linux ext4',
                'ufs': 'BSD UFS',
                'iso9660': 'ISO 9660 (read-only)',
                'udf': 'Universal Disk Format',
                'gfs': 'Linux GFS',
                'gfs2': 'Linux GFS2',
                'vfat': 'Windows FAT',
                'hfs+': 'macOS HFS+',
                'xfs': 'Linux XFS',
                'ocfs2': 'Linux OCFS2',
                'vmfs': 'VMWare VMFS',
            },
            'target': {
                'path': True,
            },
            'source': {
                'device': True,
            },
            'features': {
                'cow': True,
            },
        },
        'volume': {
            'formats': FILE_VOLUME_FORMATS,
            'target': {
                'nocow': True,
            },
        },
    },
    'netfs': {
        'type': 'netfs',
        'name': 'Network filesystem pool',
        'pool': {
            'formats': {
                'auto': 'Automatically determine format',
                'nfs': 'NFS',
                'gluster': 'GlusterFS FUSE',
                'cifs': 'SMB/CIFS',
            },
            'target': {
                'path': True,
            },
            'source': {
                'host': True,
                'dir': True,
                'protocol': False,
            },
        },
        'volume': {
            'formats': FILE_VOLUME_FORMATS,
        },
    },
    'logical': {
        'type': 'logical',
        'name': 'LVM volume group pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
            'source': {
                'device': True,
            },
        },
        'volume': {
            'formats': dict(),
        },
    },
    'disk': {
        'type': 'disk',
        'name': 'Disk pool',
        'pool': {
            'formats': {
                'dos': 'DOS master boot record',
                'gpt': 'EFI GUID partition table',
                'dvh': 'SGI disk volume header',
                'mac': 'Apple partition map',
                'bsd': 'BSD disklabel',
                'pc98': 'PC-98 partition table',
                'sun': 'Sun partition table',
            },
            'target': {
                'path': True,
            },
            'source': {
                'device': True,
            },
        },
        'volume': {
            'formats': {
                'none': 'No partition ID',
                'linux': 'Linux data partition',
                'fat16': 'FAT-16 partition',
                'fat32': 'FAT-32 partition',
                'linux-swap': 'Linux swap partition',
                'linux-lvm': 'Linux LVM partition',
                'linux-raid': 'Linux RAID partition',
                'extended': 'DOS extended partition',
            },
        },
    },
    'iscsi': {
        'type': 'iscsi',
        'name': 'iSCSI pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
            'source': {
                'host': True,
                'device': True,
            },
        },
        'volume': {
            'formats': dict(),
        },
    },
    'iscsi-direct': {
        'type': 'iscsi-direct',
        'name': 'iSCSI direct pool',
        'pool': {
            'formats': dict(),
            'target': dict(),
            'source': {
                'host': True,
                'device': True,
                'initiator': True,
            },
        },
        'volume': {
            'formats': dict(),
        },
    },
    'scsi': {
        'type': 'scsi',
        'name': 'SCSI pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
            'source': {
                'adapter': True,
            },
        },
        'volume': {
            'formats': dict(),
        },
    },
    'multipath': {
        'type': 'multipath',
        'name': 'Multipath pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
        },
        'volume': {
            'formats': dict(),
        },
    },
    'rbd': {
        'type': 'rbd',
        'name': 'Rados block device pool',
        'pool': {
            'formats': dict(),
            'target': dict(),
            'source': {
                'name': True,
                'host': True,
            },
        },
        'volume': {
            'formats': {
                'raw': 'Raw disk image',
            },
        },
    },
    'gluster': {
        'type': 'gluster',
        'name': 'GlusterFS volume pool',
        'pool': {
            'formats': dict(),
            'target': dict(),
            'source': {
                'name': True,
                'host': True,
                'dir': True,
            },
        },
        'volume': {
            'formats': FILE_VOLUME_FORMATS,
        },
    },
    'zfs': {
        'type': 'zfs',
        'name': 'ZFS pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
            'source': {
                'name': True,
                'device': True,
            },
        },
        'volume': {
            'formats': dict(),
        },
    },
    'vstorage': {
        'type': 'vstorage',
        'name': 'Virtuozzo storage pool',
        'pool': {
            'formats': dict(),
            'target': {
                'path': True,
            },
            'source': {
                'name': True,
            },
        },
        'volume': {
            'formats': FILE_VOLUME_FORMATS,
        },
    },
}
