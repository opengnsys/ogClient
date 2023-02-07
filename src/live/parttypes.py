#
# Copyright (C) 2023 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import fdisk

GPT_PARTTYPES = {
    'LINUX':    '0FC63DAF-8483-4772-8E79-3D69D8477DE4',
    'NTFS':     'EBD0A0A2-B9E5-4433-87C0-68B6B72699C7',
    'EFI':      'C12A7328-F81F-11D2-BA4B-00A0C93EC93B',
    'HFS':      '48465300-0000-11AA-AA11-00306543ECAC',
}

DOS_PARTTYPES = {
    'EXTENDED': 0x0f,
    'EMPTY':    0x00,
    'LINUX':    0x83,
    'CACHE':    0x83,
    'NTFS':     0x07,
    'HFS':      0xaf,
}


def get_dos_parttype(cxt, ptype_str):
    l = cxt.label
    code = DOS_PARTTYPES.get(ptype_str, 0x0)
    parttype = l.get_parttype_from_code(code)
    return parttype


def get_gpt_parttype(cxt, ptype_str):
    l = cxt.label
    uuid = GPT_PARTTYPES.get(ptype_str, GPT_PARTTYPES['LINUX'])
    parttype = l.get_parttype_from_string(uuid)
    return parttype


def get_parttype(cxt, ptype_str):
    if not cxt:
        raise RuntimeError('No libfdisk context')
    if not cxt.label or cxt.label.name not in ['dos', 'gpt']:
        raise RuntimeError('Unknown libfdisk label')
    if type(ptype_str) != str:
        raise RuntimeError('Invalid partition type')

    if cxt.label.name == 'dos':
        return get_dos_parttype(cxt, ptype_str)
    elif cxt.label.name == 'gpt':
        return get_gpt_parttype(cxt, ptype_str)
    else:
        raise RuntimeError('BUG: Invalid partition label')
