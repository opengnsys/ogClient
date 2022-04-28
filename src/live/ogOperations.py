#
# Copyright (C) 2020-2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

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

    def _refresh_part_setup_cache(self, cxt, pa, part_setup, cache):
        padev = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_DEVICE)
        if padev == cache:
            part_setup['filesystem'] = 'CACHE'
            part_setup['code'] = 'ca'


    def parseGetConf(self, out):
        parsed = {'serial_number': '',
              'disk_setup': list(),
              'partition_setup': list()}
        configs = out.split('\n')
        for line in configs[:-1]:
            if 'ser=' in line:
                parsed['serial_number'] = line.partition('ser=')[2]
            else:
                part_setup = {}
                params = dict(param.split('=') for param in line.split('\t'))
                # Parse partition configuration.
                part_setup['disk'] = params['disk']
                part_setup['disk_type'] = params.get('dtype', '')
                part_setup['partition'] = params['par']
                part_setup['code'] = params['cpt']
                part_setup['filesystem'] = params['fsi']
                part_setup['os'] = params['soi']
                part_setup['size'] = params['tam']
                part_setup['used_size'] = params['uso']
                if part_setup['partition'] == '0':
                    parsed['disk_setup'].append(part_setup)
                else:
                    parsed['partition_setup'].append(part_setup)
        return parsed

    def poweroff(self):
        if os.path.exists('/scripts/oginit'):
            cmd = f'source {ogClient.OG_PATH}etc/preinit/loadenviron.sh; ' \
                  f'{ogClient.OG_PATH}scripts/poweroff'
            subprocess.call([cmd], shell=True, executable=OG_SHELL)
        else:
            subprocess.call(['/sbin/poweroff'])

    def reboot(self):
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
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser(self._url)

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
            raise ValueError('Error: Incorrect command value')

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
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

        software = ''
        with open(path, 'r') as f:
            software = f.read()
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
            raise ValueError('Error: Incorrect command value')

        self._restartBrowser(self._url)

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
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser(self._url)

        return self.parseGetConf(result.decode('utf-8'))

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
            raise ValueError('Error: Incorrect command value')

        cmd_get_conf = f'{ogClient.OG_PATH}interfaceAdm/getConfiguration'
        result = subprocess.check_output([cmd_get_conf], shell=True)
        self._restartBrowser(self._url)

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
            raise ValueError('Error: Incorrect command value')

        if ogRest.proc.returncode != 0:
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

        return image_info

    def refresh(self, ogRest):
        self._restartBrowser(self._url_log)

        cache = cache_probe()
        disks = get_disks()
        parsed = { 'serial_number': '',
                'disk_setup': [],
                'partition_setup': []
        }

        for num_disk, disk in enumerate(get_disks(), start=1):
            print(disk)
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
        self._restartBrowser(self._url)

        return parsed

    def probe(self, ogRest):

        interface = os.getenv('DEVICE')
        speed = ethtool(interface)

        return {'status': 'OPG' if ogRest.state != ThreadState.BUSY else 'BSY',
                'speed': speed}
