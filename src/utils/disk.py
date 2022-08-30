#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os

import fdisk


def get_disks():
    """
    Walks /sys/block/ and returns files starting with 'sd',
    'nvme' or 'vd'
    """
    return sorted([ dev for dev in os.listdir('/sys/block/')
                    if dev.startswith('sd')
                    or dev.startswith('nvme')
                    or dev.startswith('vd')])


def get_partition_device(disknum, partnum):
    """
    Returns the device path, given a disk and partition number
    """
    disk = get_disks()[disknum-1]
    cxt = fdisk.Context(f'/dev/{disk}')

    for pa in cxt.partitions:
        if pa.partno == partnum - 1:
            return cxt.partition_to_string(pa, fdisk.FDISK_FIELD_DEVICE)

    raise ValueError('No such partition')
