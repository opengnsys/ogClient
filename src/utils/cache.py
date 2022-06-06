#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import logging
import os

from src.utils.fs import mount_mkdir, umount
from src.utils.net import getifaddr
from src.utils.probe import cache_probe

OGIMG='/opt/opengnsys/images/'
OGCACHE_MOUNTPOINT='/opt/opengnsys/cache'
OGCLIENT_LOG_CACHE='/opt/opengnsys/log/{ip}.cache.txt'

def mount_cache():
    """
    Probes for cache and mounts if succesful.

    Returns the mountpoint or an empty string.
    """
    cache_dev = cache_probe()

    if cache_dev:
        # cache_target = cache_dev.replace('dev', 'mnt')
        mount_mkdir(cache_dev, OGCACHE_MOUNTPOINT)
        return OGCACHE_MOUNTPOINT

    return ''

def umount_cache():
    """
    If OGCACHE_MOUNTPOINT is a mountpoint, umounts.
    If not, does nothing.
    """
    if os.path.ismount(OGCACHE_MOUNTPOINT):
        umount(OGCACHE_MOUNTPOINT)

def write_cache_txt(content):
    """
    Dumps content to /opt/opengnsys/log/{ip}.cache.txt
    """
    client_ip = getifaddr(os.getenv('DEVICE'))
    with open(OGCLIENT_LOG_CACHE.format(ip=client_ip), 'w') as f:
        logging.debug('Writing cache contents to %s.cache.txt', client_ip)
        f.write(content)

def generate_cache_txt():
    """
    If no OpenGnsys cache partition is detected this function will
    do nothing.

    Generates a *.cache.txt file from a given path.

    A .cache.txt file is just a comma separated list of
    the files contained in the images folder in the OpenGnsys cache.
    """
    cache_path = mount_cache()

    if cache_path:
        try:
            files = os.listdir(f'{cache_path}{OGIMG}')
        except FileNotFoundError:
            return
        content = ','.join(files)
        write_cache_txt(content)
