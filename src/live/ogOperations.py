#
# Copyright (C) 2020-2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import hashlib
import logging
import os
import subprocess
import shlex
import shutil

from subprocess import Popen, PIPE

import fdisk

from src.ogClient import ogClient
from src.ogRest import ThreadState
from src.live.partcodes import GUID_MAP
from src.live.parttypes import get_parttype

from src.utils.legacy import *
from src.utils.net import ethtool
from src.utils.menu import generate_menu
from src.utils.fs import *
from src.utils.probe import os_probe, cache_probe
from src.utils.disk import *
from src.utils.cache import generate_cache_txt, umount_cache, init_cache
from src.utils.tiptorrent import *


OG_SHELL = '/bin/bash'

class OgLiveOperations:
    def __init__(self, config):
        self._url = config['opengnsys']['url']
        self._url_log = config['opengnsys']['url_log']
        self._smb_user = config['samba']['user']
        self._smb_pass = config['samba']['pass']

    def _restartBrowser(self, url):
        try:
            proc = subprocess.call(["pkill", "-9", "browser"])
            proc = subprocess.Popen(["browser", "-qws", url])
        except:
            logging.error('Cannot restart browser')
            raise ValueError('Error: cannot restart browser')

    def _refresh_payload_disk(self, cxt, part_setup, num_disk):
        part_setup['disk'] = str(num_disk)
        part_setup['disk_type'] = 'DISK'
        part_setup['partition'] = '0'
        part_setup['filesystem'] = ''
        part_setup['os'] = ''
        part_setup['size'] = str(cxt.nsectors * cxt.sector_size // 1024)
        part_setup['used_size'] = '0'
        if not cxt.label:
            part_setup['code'] = '0'
        else:
            part_setup['code'] = '2' if cxt.label.name == 'gpt' else '1'

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

    def _compute_md5(self, path, bs=2**20):
        m = hashlib.md5()
        with open(path, 'rb') as f:
            while True:
                buf = f.read(bs)
                if not buf:
                    break
                m.update(buf)
        return m.hexdigest()

    def _write_md5_file(self, path):
        if not os.path.exists(path):
            logging.error('Invalid path in _write_md5_file')
            raise ValueError('Invalid image path when computing md5 checksum')
        filename = path + ".full.sum"
        dig = self._compute_md5(path)
        with open(filename, 'w') as f:
            f.write(dig)

    def _copy_image_to_cache(self, image_name):
        """
        Copies /opt/opengnsys/image/{image_name} into
        /opt/opengnsys/cache/opt/opengnsys/images/

        Implies a unicast transfer. Does not use tiptorrent.
        """
        src = f'/opt/opengnsys/images/{image_name}.img'
        dst = f'/opt/opengnsys/cache/opt/opengnsys/images/{image_name}.img'
        try:
            r = shutil.copy(src, dst)
            tip_write_csum(image_name)
        except:
            logging.error('Error copying image to cache', repo)
            raise ValueError(f'Error: Cannot copy image {image_name} to cache')

    def _restore_image_unicast(self, repo, name, devpath, cache=False):
        if ogChangeRepo(repo).returncode != 0:
            self._restartBrowser(self._url)
            logging.error('ogChangeRepo could not change repository to %s', repo)
            raise ValueError(f'Error: Cannot change repository to {repo}')
        logging.debug(f'restore_image_unicast: name => {name}')
        if cache:
            image_path = f'/opt/opengnsys/cache/opt/opengnsys/images/{name}.img'
            if (not os.path.exists(image_path) or
                not tip_check_csum(repo, name)):
                self._copy_image_to_cache(name)
        else:
            image_path = f'/opt/opengnsys/images/{name}.img'
        self._restore_image(image_path, devpath)

    def _restore_image_tiptorrent(self, repo, name, devpath):
        image_path = f'/opt/opengnsys/cache/opt/opengnsys/images/{name}.img'
        try:
            if (not os.path.exists(image_path) or
                not tip_check_csum(repo, name)):
                tip_client_get(repo, name)
        except:
            self._restartBrowser(self._url)
            raise ValueError('Error before restoring image')
        self._restore_image(image_path, devpath)

    def _restore_image(self, image_path, devpath):
        logging.debug(f'Restoring image at {image_path} into {devpath}')
        cmd_lzop = shlex.split(f'lzop -dc {image_path}')
        cmd_pc = shlex.split(f'partclone.restore -d0 -C -I -o {devpath}')
        cmd_mbuffer = shlex.split('mbuffer -q -m 40M') if shutil.which('mbuffer') else None

        if not os.path.exists(image_path):
            logging.error('f{image_path} does not exist, exiting.')
            raise ValueError(f'Error: Image not found at {image_path}')

        with open('/tmp/command.log', 'wb', 0) as logfile:
            proc_lzop = subprocess.Popen(cmd_lzop,
                                         stdout=subprocess.PIPE)
            proc_pc = subprocess.Popen(cmd_pc,
                                       stdin=proc_lzop.stdout,
                                       stderr=logfile)
            proc_lzop.stdout.close()
            proc_pc.communicate()

    def _ogbrowser_clear_logs(self):
        logfiles = ['/tmp/command.log', '/tmp/session.log']
        for logfile in logfiles:
            with open(logfile, 'wb', 0) as f:
                f.truncate(0)

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

        self._ogbrowser_clear_logs()
        self._restartBrowser(self._url_log)

        diskname = get_disks()[int(disk)-1]
        cxt = fdisk.Context(f'/dev/{diskname}',
                            details=True)

        if table_type == 'MSDOS':
            cxt.create_disklabel('dos')
        elif table_type == 'GPT':
            cxt.create_disklabel('gpt')

        for part in partlist:
            logging.debug(f'Adding partition: {part}')
            if part["code"] == 'EMPTY':
                continue
            if ogRest.terminated:
                break
            if part["code"] == 'CACHE':
                umount_cache()

            pa = fdisk.Partition(start_follow_default=True,
                                 end_follow_default=False,
                                 partno_follow_default=False)
            parttype = get_parttype(cxt, part["code"])
            size = int(part["size"])
            pa.size = (size * (1 << 10)) // cxt.sector_size
            pa.partno = int(part["partition"]) - 1
            pa.type = parttype
            cxt.add_partition(pa)

        cxt.write_disklabel()
        subprocess.run('partprobe')

        for part in partlist:
            if part["filesystem"] == 'EMPTY':
                continue
            partition = int(part["partition"])
            fs = part["filesystem"].lower()
            if fs == 'cache':
                mkfs('ext4', int(disk), partition, label='CACHE')
                init_cache()
            else:
                mkfs(fs, int(disk), partition)

        logging.info('Setup command OK')
        result = self.refresh(ogRest)

        self._restartBrowser(self._url)

        return result

    def image_restore(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        ctype = request.getType()
        profile = request.getProfile()
        cid = request.getId()
        partdev = get_partition_device(int(disk), int(partition))

        self._ogbrowser_clear_logs()
        self._restartBrowser(self._url_log)

        logging.debug('Image restore params:')
        logging.debug(f'\tname: {name}')
        logging.debug(f'\trepo: {repo}')
        logging.debug(f'\tprofile: {profile}')
        logging.debug(f'\tctype: {ctype}')

        if shutil.which('restoreImageCustom'):
            restoreImageCustom(repo, name, disk, partition, ctype)
        elif 'UNICAST' in ctype:
            cache = 'DIRECT' not in ctype
            self._restore_image_unicast(repo, name, partdev, cache)
        elif ctype == 'TIPTORRENT':
            self._restore_image_tiptorrent(repo, name, partdev)

        output = configureOs(disk, partition)

        self.refresh(ogRest)

        logging.info('Image restore command OK')
        return output

    def image_create(self, path, request, ogRest):
        disk = int(request.getDisk())
        partition = int(request.getPartition())
        name = request.getName()
        repo = request.getRepo()
        cmd_software = f'{ogClient.OG_PATH}interfaceAdm/InventarioSoftware {disk} ' \
                   f'{partition} {path}'
        image_path = f'/opt/opengnsys/images/{name}.img'

        self._ogbrowser_clear_logs()
        self._restartBrowser(self._url_log)

        if ogChangeRepo(repo).returncode != 0:
            self._restartBrowser(self._url)
            logging.error('ogChangeRepo could not change repository to %s', repo)
            raise ValueError(f'Error: Cannot change repository to {repo}')

        try:
            ogRest.proc = subprocess.Popen([cmd_software],
                               stdout=subprocess.PIPE,
                               shell=True,
                               executable=OG_SHELL)
            (output, error) = ogRest.proc.communicate()
        except:
            self._restartBrowser(self._url)
            logging.error('Exception when running software inventory subprocess')
            raise ValueError('Error: Incorrect command value')

        if ogRest.terminated:
            return

        try:
            diskname = get_disks()[disk-1]
            cxt = fdisk.Context(f'/dev/{diskname}', details=True)
            pa = None

            for i, p in enumerate(cxt.partitions):
                if (p.partno + 1) == partition:
                    pa = cxt.partitions[i]

            if pa is None:
                self._restartBrowser(self._url)
                logging.error('Target partition not found')
                raise ValueError('Target partition number not found')

            padev = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_DEVICE)
            fstype = cxt.partition_to_string(pa, fdisk.FDISK_FIELD_FSTYPE)
            if not fstype:
                    logging.error('No filesystem detected. Aborting image creation.')
                    raise ValueError('Target partition has no filesystem present')

            cambiar_acceso(user=self._smb_user, pwd=self._smb_pass)
            ogCopyEfiBootLoader(disk, partition)
            ogReduceFs(disk, partition)

            cmd1 = shlex.split(f'partclone.{fstype} -I -C --clone -s {padev} -O -')
            cmd2 = shlex.split(f'lzop -1 -fo {image_path}')

            logfile = open('/tmp/command.log', 'wb', 0)

            p1 = Popen(cmd1, stdout=PIPE, stderr=logfile)
            p2 = Popen(cmd2, stdin=p1.stdout)
            p1.stdout.close()

            try:
                    retdata = p2.communicate()
            except OSError as e:
                    logging.error('Unexpected error when running partclone and lzop commands')
            finally:
                    logfile.close()
                    p2.terminate()
                    p1.poll()

            logging.info(f'partclone process exited with code {p1.returncode}')
            logging.info(f'lzop process exited with code {p2.returncode}')

            ogExtendFs(disk, partition)

            image_info = ogGetImageInfo(image_path)
        except:
            self._restartBrowser(self._url)
            logging.error('Exception when running "image create" subprocess')
            raise ValueError('Error: Incorrect command value')

        self._write_md5_file(f'/opt/opengnsys/images/{name}.img')

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
                cxt = fdisk.Context(device=f'/dev/{disk}', details=True)
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
