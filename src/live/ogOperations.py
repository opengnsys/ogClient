#
# Copyright (C) 2020-2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import logging
import os
import subprocess

import fdisk

from src.ogClient import ogClient
from src.ogRest import ThreadState
from src.live.partcodes import GUID_MAP

from src.utils.net import ethtool
from src.utils.menu import generate_menu
from src.utils.fs import mount_mkdir, umount, get_usedperc
from src.utils.probe import os_probe, cache_probe
from src.utils.disk import get_disks
from src.utils.cache import generate_cache_txt


OG_SHELL = '/bin/bash'

class OgLiveOperations:
    def __init__(self, config):
        self._url = config['opengnsys']['url']
        self._url_log = config['opengnsys']['url_log']

    def _restartBrowser(self, url):
        try:
            proc = subprocess.call(["pkill", "-9", "browser"])
            proc = subprocess.Popen(["browser", "-qws", url])
        except:
            raise ValueError('Error: cannot restart browser')

    def _refresh_payload_disk(self, cxt, part_setup, num_disk):
        part_setup['disk'] = str(num_disk)
        part_setup['disk_type'] = 'DISK'
        part_setup['code'] = '2' if cxt.label.name == 'gpt' else '1'
        part_setup['partition'] = '0'
        part_setup['filesystem'] = ''
        part_setup['os'] = ''
        part_setup['size'] = str(cxt.nsectors * cxt.sector_size // 1024)
        part_setup['used_size'] = '0'

    def _refresh_payload_partition(self, cxt, pa, part_setup, disk):
        parttype = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_TYPEID)
        fstype = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_FSTYPE)
        padev = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_DEVICE)
        size = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_SIZE)
        partnum = pa.partno + 1
        source = padev
        target = padev.replace('dev', 'mnt')

        if cxt.label.name == 'gpt':
            code = GUID_MAP.get(parttype, 0x0)
        else:
            code = int(parttype, base=16)

        if mount_mkdir(source, target):
            probe_result = os_probe(target)
            part_setup['os'] = probe_result
            part_setup['used_size'] = get_usedperc(target)
            umount(target)
        else:
            part_setup['os'] = ''
            part_setup['used_size'] = '0'


        part_setup['disk_type'] = ''
        part_setup['partition'] = str(partnum)
        part_setup['filesystem'] = fstype.upper() if fstype else 'EMPTY'
        # part_setup['code'] = hex(code).removeprefix('0x')
        part_setup['code'] = hex(code)[2:]
        part_setup['size'] = str(int(size) // 1024)

        if (part_setup['filesystem'] == 'VFAT'):
            part_setup['filesystem'] = 'FAT32'

    def _refresh_part_setup_cache(self, cxt, pa, part_setup, cache):
        padev = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_DEVICE)
        if padev == cache:
            part_setup['filesystem'] = 'CACHE'
            part_setup['code'] = 'ca'

    def poweroff(self):
        logging.info('Powering off client')
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogClient.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogClient.OG_PATH}scripts/poweroff'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/poweroff'])

    def reboot(self):
        logging.info('Rebooting client')
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogClient.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogClient.OG_PATH}scripts/reboot'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/reboot'])

    def shellrun(self, request, ogRest):
        cmd = request.getrun()
        cmds = cmd.split(";|\n\r")

        self._restartBrowser(self._url_log)

        try:
            ogRest.proc = subprocess.Popen(cmds,
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            logging.error('Exception when running "shell run" subprocess')
            raise ValueError('Error: Incorrect command value')

        if ogRest.proc.returncode != 0:
            logging.warn('Non zero exit code when running: %s', ' '.join(cmds))
        else:
            logging.info('Shell run command OK')

        self.refresh(ogRest)

        return output.decode('utf-8')

    def session(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        cmd = f'{ogClient.OG_PATH}interfaceAdm/IniciarSesion {disk} {partition}'

        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            logging.error('Exception when running session subprocess')
            raise ValueError('Error: Incorrect command value')

        logging.info('Starting OS at disk %s partition %s', disk, partition)
        return output.decode('utf-8')

    def software(self, request, path, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()

        self._restartBrowser(self._url_log)

        try:
            cmd = f'{ogClient.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                  f'{partition} {path}'

            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            logging.error('Exception when running software inventory subprocess')
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

        software = ''
        with open(path, 'r') as f:
            software = f.read()

        logging.info('Software inventory command OK')
        return software

    def hardware(self, path, ogRest):
        self._restartBrowser(self._url_log)

        try:
            cmd = f'{ogClient.OG_PATH}interfaceAdm/InventarioHardware {path}'
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            logging.error('Exception when running hardware inventory subprocess')
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

        logging.info('Hardware inventory command OK')
        return output.decode('utf-8')

    def setup(self, request, ogRest):
        table_type = request.getType()
        disk = request.getDisk()
        cache = request.getCache()
        cache_size = request.getCacheSize()
        partlist = request.getPartitionSetup()
        cfg = f'dis={disk}*che={cache}*tch={cache_size}!'

        for part in partlist:
            cfg += f'par={part["partition"]}*cpt={part["code"]}*' \
                   f'sfi={part["filesystem"]}*tam={part["size"]}*' \
                   f'ope={part["format"]}%'

            if ogRest.terminated:
                break

        cmd = f'{ogClient.OG_PATH}interfaceAdm/Configurar {table_type} {cfg}'
        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            logging.error('Exception when running setup subprocess')
            raise ValueError('Error: Incorrect command value')

        logging.info('Setup command OK')
        result = self.refresh(ogRest)

        return result

    def image_restore(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        ctype = request.getType()
        profile = request.getProfile()
        cid = request.getId()
        cmd = f'{ogClient.OG_PATH}interfaceAdm/RestaurarImagen {disk} {partition} ' \
              f'{name} {repo} {ctype}'

        self._restartBrowser(self._url_log)

        try:
            ogRest.proc = subprocess.Popen([cmd],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
            if (ogRest.proc.returncode):
                raise Exception
        except:
            logging.error('Exception when running image restore subprocess')
            raise ValueError('Error: Incorrect command value')

        self.refresh(ogRest)

        logging.info('Image restore command OK')
        return output.decode('utf-8')

    def image_create(self, path, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        cmd_software = f'{ogClient.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                   f'{partition} {path}'
        cmd_create_image = f'{ogClient.OG_PATH}interfaceAdm/CrearImagen {disk} ' \
                   f'{partition} {name} {repo}'

        self._restartBrowser(self._url_log)

        try:
            ogRest.proc = subprocess.Popen([cmd_software],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            logging.error('Exception when running software inventory subprocess')
            raise ValueError('Error: Incorrect command value')

        if ogRest.terminated:
            return

        try:
            ogRest.proc = subprocess.Popen([cmd_create_image],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            ogRest.proc.communicate()
        except:
            logging.error('Exception when running "image create" subprocess')
            raise ValueError('Error: Incorrect command value')

        if ogRest.proc.returncode != 0:
            logging.warn('Image creation failed')
            raise ValueError('Error: Image creation failed')

        with open('/tmp/image.info') as file_info:
            line = file_info.readline().rstrip()

        image_info = {}

        (image_info['clonator'],
         image_info['compressor'],
         image_info['filesystem'],
         image_info['datasize'],
         image_info['clientname']) = line.split(':', 5)

        os.remove('/tmp/image.info')

        self._restartBrowser(self._url)

        logging.info('Image creation command OK')
        return image_info

    def refresh(self, ogRest):
        self._restartBrowser(self._url_log)

        cache = cache_probe()
        disks = get_disks()
        interface = os.getenv('DEVICE')
        link = ethtool(interface)
        parsed = { 'serial_number': '',
                'disk_setup': [],
                'partition_setup': [],
                'link': link
        }

        for num_disk, disk in enumerate(get_disks(), start=1):
            logging.debug('refresh: processing %s', disk)
            part_setup = {}
            try:
                cxt = fdisk.Context(device=f'/dev/{disk}')
            except:
                continue

            self._refresh_payload_disk(cxt, part_setup, num_disk)
            parsed['disk_setup'].append(part_setup)

            for pa in cxt.partitions:
                part_setup = part_setup.copy()
                self._refresh_payload_partition(cxt, pa, part_setup, disk)
                self._refresh_part_setup_cache(cxt, pa, part_setup, cache)
                parsed['partition_setup'].append(part_setup)

        generate_menu(parsed['partition_setup'])
        generate_cache_txt()
        self._restartBrowser(self._url)

        logging.info('Sending response to refresh request')
        return parsed

    def probe(self, ogRest):

        interface = os.getenv('DEVICE')
        speed = ethtool(interface)

        return {'status': 'OPG' if ogRest.state != ThreadState.BUSY else 'BSY',
                'speed': speed}
