#
# Copyright (C) 2022 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os

def get_disks():
    """
    Walks /sys/block/ and returns files starting with 'sd',
    'nvme' or 'vd'
    """
    return sorted([ dev for dev in os.listdir('/sys/block/')
                    if dev.startswith('sd')
                    or dev.startswith('nvme')
                    or dev.startswith('vd')])
