#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import logging
import os
import subprocess
import shlex

from subprocess import DEVNULL, PIPE, STDOUT

import psutil

from src.utils.disk import get_partition_device


def find_mountpoint(path):
    """
    Returns mountpoint of a given path
    """
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path


def mount_mkdir(source, target):
    """
    Mounts and creates the mountpoint directory if it's not present.

    Return True if mount is sucessful or if target is already a mountpoint.
    """
    if not os.path.exists(target):
        os.mkdir(target)

    if not os.path.ismount(target):
        return mount(source, target)
    else:
        return True

    return False


def mount(source, target):
    """
    Mounts source into target directoru using mount(8).

    Return true if exit code is 0. False otherwise.
    """
    cmd = f'mount {source} {target}'
    proc = subprocess.run(cmd.split(), stderr=DEVNULL)

    return not proc.returncode


def umount(target):
    """
    Umounts target using umount(8).

    Return true if exit code is 0. False otherwise.
    """
    cmd = f'umount {target}'
    proc = subprocess.run(cmd.split(), stderr=DEVNULL)

    return not proc.returncode


def get_usedperc(mountpoint):
    """
    Returns percetage of used filesystem as decimal number.
    """
    try:
        total, used, free, perc = psutil.disk_usage(mountpoint)
    except FileNotFoundError:
        return '0'
    return str(perc)


def ogReduceFs(disk, part):
    """
    Bash function 'ogReduceFs' wrapper
    """
    proc = subprocess.run(f'ogReduceFs {disk} {part}',
                          shell=True, stdout=PIPE,
                          encoding='utf-8')
    if proc.returncode != 0:
        logging.warn(f'ogReduceFS exited with non zero code: {proc.returncode}')
    subprocess.run(f'ogUnmount {disk} {part}',
                   shell=True)


def ogExtendFs(disk, part):
    """
    Bash function 'ogExtendFs' wrapper
    """
    subprocess.run(f'ogMount {disk} {part}',
                   shell=True)
    proc = subprocess.run(f'ogExtendFs {disk} {part}',
                          shell=True)
    if proc.returncode != 0:
        logging.warn(f'ogExtendFs exited with non zero code: {proc.returncode}')


def mkfs(fs, disk, partition, label=None):
    """
    Install any supported filesystem. Target partition is specified a disk
    number and partition number. This function uses utility functions to
    translate disk and partition number into a partition device path.

    If filesystem and partition are correct, calls the corresponding mkfs_*
    function with the partition device path. If not, ValueError is raised.
    """
    logging.debug(f'mkfs({fs}, {disk}, {partition}, {label})')
    fsdict = {
        'ext4': mkfs_ext4,
        'ntfs': mkfs_ntfs,
        'fat32': mkfs_fat32,
    }

    if fs not in fsdict:
        logging.warn(f'mkfs aborted, invalid target filesystem.')
        raise ValueError('Invalid target filesystem')

    try:
        partdev = get_partition_device(disk, partition)
    except ValueError as e:
        logging.warn(f'mkfs aborted, invalid partition.')
        raise e

    fsdict[fs](partdev, label)


def mkfs_ext4(partdev, label=None):
    if label:
        cmd = shlex.split(f'mkfs.ext4 -L {label} -F {partdev}')
    else:
        cmd = shlex.split(f'mkfs.ext4 -F {partdev}')
    with open('/tmp/command.log', 'wb', 0) as logfile:
        subprocess.run(cmd,
                       stdout=logfile,
                       stderr=STDOUT)


def mkfs_ntfs(partdev, label=None):
    if label:
        cmd = shlex.split(f'mkfs.ntfs -f -L {label} {partdev}')
    else:
        cmd = shlex.split(f'mkfs.ntfs -f {partdev}')
    with open('/tmp/command.log', 'wb', 0) as logfile:
        subprocess.run(cmd,
                       stdout=logfile,
                       stderr=STDOUT)


def mkfs_fat32(partdev, label=None):
    if label:
        cmd = shlex.split(f'mkfs.vfat -n {label} -F32 {partdev}')
    else:
        cmd = shlex.split(f'mkfs.vfat -F32 {partdev}')
    with open('/tmp/command.log', 'wb', 0) as logfile:
        subprocess.run(cmd,
                       stdout=logfile,
                       stderr=STDOUT)
