#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import socket
import errno
import select
import json
import subprocess
import shutil
import os
import guestfs
import hivex
import pathlib
import re
import math
import sys

class OgQMP:
    QMP_TIMEOUT = 5

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        try:
            self.sock.connect((ip, port))
        except socket.error as err:
            if err.errno == errno.ECONNREFUSED:
                raise Exception('cannot connect to qemu')
            elif err.errno == errno.EINPROGRESS:
                pass

        readset = [ self.sock ]
        writeset = [ self.sock ]
        readable, writable, exception = select.select(readset,
                                                      writeset,
                                                      [],
                                                      OgQMP.QMP_TIMEOUT)
        if self.sock in writable:
            try:
                self.sock.connect((self.ip, self.port))
                print("connected")
            except socket.error as err:
                if err.errno == errno.ECONNREFUSED:
                    raise Exception('cannot connect to qemu')

    def talk(self, data):
        try:
            self.sock.send(bytes(data, 'utf-8'))
        except:
            raise Exception('cannot talk to qemu')

        readset = [ self.sock ]
        readable, writable, exception = select.select(readset, [], [], 5)
        if self.sock in readable:
            try:
                out = self.sock.recv(4096).decode('utf-8')
            except socket.error as err:
                raise Exception('cannot talk to qemu')
        else:
            raise Exception('timeout when talking to qemu')
        return out

    def disconnect(self):
        self.sock.close()

class OgVirtualOperations:
    def __init__(self):
        self.IP = '127.0.0.1'
        self.VIRTUAL_PORT = 4444
        self.USABLE_DISK = 0.75
        self.OG_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.OG_IMAGES_PATH = f'{self.OG_PATH}/images'
        self.OG_PARTITIONS_PATH = f'{self.OG_PATH}/partitions'

        if not os.path.exists(self.OG_IMAGES_PATH):
            os.mkdir(self.OG_IMAGES_PATH, mode=0o755)
        if not os.path.exists(self.OG_PARTITIONS_PATH):
            os.mkdir(self.OG_PARTITIONS_PATH, mode=0o755)

    def poweroff(self):
        try:
            qmp = OgQMP(self.IP, self.VIRTUAL_PORT)
            qmp.talk(str({"execute": "qmp_capabilities"}))
            qmp.talk(str({"execute": "system_powerdown"}))
            qmp.disconnect()
        except:
            pass

    def reboot(self):
        try:
            qmp = OgQMP(self.IP, self.VIRTUAL_PORT)
            qmp.talk(str({"execute": "qmp_capabilities"}))
            qmp.talk(str({"execute": "system_reset"}))
            qmp.disconnect()
        except:
            pass

    def execCMD(self, request, ogRest):
        # TODO Implement.
        raise NotImplementedError

    def session(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()

        available_ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        available_ram_mib = available_ram / 1024 ** 2
        # Calculate the lower power of 2 amout of RAM memory for the VM.
        vm_ram_mib = 2 ** math.floor(math.log(available_ram_mib) / math.log(2))

        cmd = (f'qemu-system-x86_64 -hda {self.OG_PARTITIONS_PATH}/disk{disk}_part{partition}.qcow2 '
               f'-qmp tcp:localhost:4444,server,nowait --enable-kvm '
               f'-display gtk -cpu host -m {vm_ram_mib}M -boot c -full-screen')
        subprocess.Popen([cmd], shell=True)

    def refresh(self, ogRest):
        path = f'{self.OG_PATH}/partitions.json'
        try:
            with open(path, 'r+') as f:
                data = json.loads(f.read())
                for part in data['partition_setup']:
                    if len(part['virt-drive']) > 0:
                        if not os.path.exists(part['virt-drive']):
                            part['code'] = '',
                            part['filesystem'] = 'EMPTY'
                            part['os'] = ''
                            part['size'] = 0
                            part['used_size'] = 0
                            part['virt-drive'] = ''
                            continue
                        g = guestfs.GuestFS(python_return_dict=True)
                        g.add_drive_opts(part['virt-drive'],
                                         format="qcow2",
                                         readonly=0)
                        g.launch()
                        devices = g.list_devices()
                        assert(len(devices) == 1)
                        partitions = g.list_partitions()
                        assert(len(partitions) == 1)
                        g.mount(partitions[0], '/')
                        used_disk = g.du('/')
                        g.umount_all()
                        total_size = g.disk_virtual_size(part['virt-drive']) / 1024
                        part['used_size'] = int(100 * used_disk / total_size)
                        part['size'] = total_size
                        root = g.inspect_os()
                        if len(root) == 1:
                            part['os'] = f'{g.inspect_get_distro(root[0])} ' \
                                         f'{g.inspect_get_product_name(root[0])}'
                        else:
                            part['os'] = ''
                        g.close()
                f.seek(0)
                f.write(json.dumps(data, indent=4))
                f.truncate()
        except FileNotFoundError:
            total_disk, used_disk, free_disk = shutil.disk_usage("/")
            free_disk = int(free_disk * self.USABLE_DISK)
            data = {'serial_number': '',
                    'disk_setup': {'disk': 1,
                                   'partition': 0,
                                   'code': '0',
                                   'filesystem': '',
                                   'os': '',
                                   'size': int(free_disk / 1024),
                                   'used_size': int(100 * used_disk / free_disk)},
                    'partition_setup': []}
            for i in range(4):
                part_json = {'disk': 1,
                             'partition': i + 1,
                             'code': '',
                             'filesystem': 'EMPTY',
                             'os': '',
                             'size': 0,
                             'used_size': 0,
                             'virt-drive': ''}
                data['partition_setup'].append(part_json)
            with open(path, 'w+') as f:
                f.write(json.dumps(data, indent=4))

        # TODO no debería ser necesario eliminar virt-drive ni transformar a strings
        for part in data['partition_setup']:
            part.pop('virt-drive')
            for k, v in part.items():
                part[k] = str(v)
        data['disk_setup'] = {k: str(v) for k, v in data['disk_setup'].items()}

        return data

    def setup(self, request, ogRest):
        path = f'{self.OG_PATH}/partitions.json'
        self.refresh(ogRest)

        part_setup = request.getPartitionSetup()
        disk = request.getDisk()

        for i, part in enumerate(part_setup):
            if int(part['format']) == 0:
                continue

            drive_path = f'{self.OG_PARTITIONS_PATH}/disk{disk}_part{part["partition"]}.qcow2'
            g = guestfs.GuestFS(python_return_dict=True)
            g.disk_create(drive_path, "qcow2", int(part['size']) * 1024)
            g.add_drive_opts(drive_path, format="qcow2", readonly=0)
            g.launch()
            devices = g.list_devices()
            assert(len(devices) == 1)
            g.part_disk(devices[0], "gpt")
            partitions = g.list_partitions()
            assert(len(partitions) == 1)
            g.mkfs(part["filesystem"].lower(), partitions[0])
            g.close()

            with open(path, 'r+') as f:
                data = json.loads(f.read())
                if part['code'] == 'LINUX':
                    data['partition_setup'][i]['code'] = '0083'
                elif part['code'] == 'NTFS':
                    data['partition_setup'][i]['code'] = '0007'
                elif part['code'] == 'DATA':
                    data['partition_setup'][i]['code'] = '00da'
                data['partition_setup'][i]['filesystem'] = part['filesystem']
                data['partition_setup'][i]['size'] = int(part['size'])
                data['partition_setup'][i]['virt-drive'] = drive_path
                f.seek(0)
                f.write(json.dumps(data, indent=4))
                f.truncate()

        return self.refresh(ogRest)

    def image_create(self, path, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        samba_config = ogRest.samba_config

        # Check if VM is running.
        try:
            qmp = OgQMP(self.IP, self.VIRTUAL_PORT)
            qmp.disconnect()
            return None
        except:
            pass

        self.refresh(ogRest)

        drive_path = f'{self.OG_PARTITIONS_PATH}/disk{disk}_part{partition}.qcow2'

        cmd = f'mount -t cifs //{repo}/ogimages {self.OG_IMAGES_PATH} -o ' \
              f'rw,nolock,serverino,acl,' \
              f'username={samba_config["user"]},' \
              f'password={samba_config["pass"]}'
        subprocess.run([cmd], shell=True)

        try:
            shutil.copy(drive_path, f'{self.OG_IMAGES_PATH}/{name}')
        except:
            return None

        subprocess.run([f'umount {self.OG_IMAGES_PATH}'], shell=True)

        return True

    def image_restore(self, request, ogRest):
        disk = request.getDisk()
        partition = request.getPartition()
        name = request.getName()
        repo = request.getRepo()
        # TODO Multicast? Unicast? Solo copia con samba.
        ctype = request.getType()
        profile = request.getProfile()
        cid = request.getId()
        samba_config = ogRest.samba_config

        # Check if VM is running.
        try:
            qmp = OgQMP(self.IP, self.VIRTUAL_PORT)
            qmp.disconnect()
            return None
        except:
            pass

        self.refresh(ogRest)

        drive_path = f'{self.OG_PARTITIONS_PATH}/disk{disk}_part{partition}.qcow2'

        if os.path.exists(drive_path):
            os.remove(drive_path)

        cmd = f'mount -t cifs //{repo}/ogimages {self.OG_IMAGES_PATH} -o ' \
              f'ro,nolock,serverino,acl,' \
              f'username={samba_config["user"]},' \
              f'password={samba_config["pass"]}'
        subprocess.run([cmd], shell=True)

        try:
            shutil.copy(f'{self.OG_IMAGES_PATH}/{name}', drive_path)
        except:
            return None

        subprocess.run([f'umount {self.OG_IMAGES_PATH}'], shell=True)

        return True

    def software(self, request, path, ogRest):
        DPKG_PATH = '/var/lib/dpkg/status'

        disk = request.getDisk()
        partition = request.getPartition()
        drive_path = f'{self.OG_PARTITIONS_PATH}/disk{disk}_part{partition}.qcow2'
        g = guestfs.GuestFS(python_return_dict=True)
        g.add_drive_opts(drive_path, readonly=1)
        g.launch()
        root = g.inspect_os()[0]

        os_type = g.inspect_get_type(root)
        os_major_version = g.inspect_get_major_version(root)
        os_minor_version = g.inspect_get_minor_version(root)
        os_distro = g.inspect_get_distro(root)

        software = []

        if 'linux' in os_type:
            g.mount_ro(g.list_partitions()[0], '/')
            try:
                g.download('/' + DPKG_PATH, 'dpkg_list')
            except:
                pass
            g.umount_all()
            if os.path.isfile('dpkg_list'):
                pkg_pattern = re.compile('Package: (.+)')
                version_pattern = re.compile('Version: (.+)')
                with open('dpkg_list', 'r') as f:
                    for line in f:
                        pkg_match = pkg_pattern.match(line)
                        version_match = version_pattern.match(line)
                        if pkg_match:
                            pkg = pkg_match.group(1)
                        elif version_match:
                            version = version_match.group(1)
                        elif line == '\n':
                            software.append(pkg + ' ' + version)
                        else:
                            continue
                os.remove('dpkg_list')
        elif 'windows' in os_type:
            g.mount_ro(g.list_partitions()[0], '/')
            hive_file_path = g.inspect_get_windows_software_hive(root)
            g.download('/' + hive_file_path, 'win_reg')
            g.umount_all()
            h = hivex.Hivex('win_reg')
            key = h.root()
            key = h.node_get_child (key, 'Microsoft')
            key = h.node_get_child (key, 'Windows')
            key = h.node_get_child (key, 'CurrentVersion')
            key = h.node_get_child (key, 'Uninstall')
            software += [h.node_name(x) for x in h.node_children(key)]
            # Just for 64 bit Windows versions, check for 32 bit software.
            if (os_major_version == 5 and os_minor_version >= 2) or \
               (os_major_version >= 6):
                key = h.root()
                key = h.node_get_child (key, 'Wow6432Node')
                key = h.node_get_child (key, 'Microsoft')
                key = h.node_get_child (key, 'Windows')
                key = h.node_get_child (key, 'CurrentVersion')
                key = h.node_get_child (key, 'Uninstall')
                software += [h.node_name(x) for x in h.node_children(key)]
            os.remove('win_reg')

        return '\n'.join(software)

    def parse_pci(self, path='/usr/share/misc/pci.ids'):
        data = {}
        with open(path, 'r') as f:
            for line in f:
                if line[0] == '#':
                    continue
                elif len(line.strip()) == 0:
                    continue
                else:
                    if line[:2] == '\t\t':
                        fields = line.strip().split(maxsplit=2)
                        data[last_vendor][last_device][(fields[0], fields[1])] = fields[2]
                    elif line[:1] == '\t':
                        fields = line.strip().split(maxsplit=1)
                        last_device = fields[0]
                        data[last_vendor][fields[0]] = {'name': fields[1]}
                    else:
                        fields = line.strip().split(maxsplit=1)
                        if fields[0] == 'ffff':
                            break
                        last_vendor = fields[0]
                        data[fields[0]] = {'name': fields[1]}
        return data

    def hardware(self, path, ogRest):
        try:
            qmp = OgQMP(self.IP, self.VIRTUAL_PORT)
            qmp.talk(str({"execute": "qmp_capabilities"}))
            pci_data = qmp.talk(str({"execute": "query-pci"}))
            mem_data = qmp.talk(str({"execute": "query-memory-size-summary"}))
            cpu_data = qmp.talk(str({"execute": "query-cpus-fast"}))
            qmp.disconnect()
        except:
            pass

        pci_data = json.loads(pci_data)
        mem_data = json.loads(mem_data)
        cpu_data = json.loads(cpu_data)

        pci_data = pci_data['return'][0]['devices']
        pci_list = self.parse_pci()
        device_names = {}
        for device in pci_data:
            vendor_id = hex(device['id']['vendor'])[2:]
            device_id = hex(device['id']['device'])[2:]
            subvendor_id = hex(device['id']['subsystem-vendor'])[2:]
            subdevice_id = hex(device['id']['subsystem'])[2:]
            description = device['class_info']['desc'].lower()
            name = ''
            try:
                name = pci_list[vendor_id]['name']
                name += ' ' + pci_list[vendor_id][device_id]['name']
                name += ' ' + pci_list[vendor_id][device_id][(subvendor_id, subdevice_id)]
            except KeyError:
                if vendor_id == '1234':
                    name = 'VGA Cirrus Logic GD 5446'
                else:
                    pass

            if 'usb' in description:
                device_names['usb'] = name
            elif 'ide' in description:
                device_names['ide'] = name
            elif 'ethernet' in description:
                device_names['net'] = name
            elif 'vga' in description:
                device_names['vga'] = name

            elif 'audio' in description or 'sound' in description:
                device_names['aud'] = name
            elif 'dvd' in description:
                device_names['cdr'] = name

        ram_size = int(mem_data['return']['base-memory']) * 2 ** -20
        device_names['mem'] = f'QEMU {int(ram_size)}MiB'

        cpu_arch = cpu_data['return'][0]['arch']
        cpu_target = cpu_data['return'][0]['target']
        cpu_cores = len(cpu_data['return'])
        device_names['cpu'] = f'CPU arch:{cpu_arch} target:{cpu_target} ' \
                              f'cores:{cpu_cores}'

        with open(path, 'w+') as f:
            f.seek(0)
            for k, v in device_names.items():
                f.write(f'{k}={v}\n')
            f.truncate()
