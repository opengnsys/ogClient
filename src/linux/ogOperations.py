#
# Copyright (C) 2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os
from pystray import Icon, Menu, MenuItem
import multiprocessing as mp
from multiprocessing import Process
from PIL import Image, ImageDraw

from src.ogRest import ThreadState


def _create_default_image():
    """
    Creates a default image for the tray icon. Use in case
    no favicon.ico is found.
    """
    width = height = 250
    color1 = (255, 255, 255)
    color2 = (255, 0, 255)

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image


def create_image():
    try:
        image = Image.open(r'./favicon.ico')
        image = Image.composite(image, Image.new('RGB', image.size, 'white'), image)
    except:
        image = _create_default_image()
    return image


def create_systray():
    menu = Menu(MenuItem('Powered by Soleta Networks!',
                         lambda icon, item: 1))
    icon = Icon('ogClient', create_image(), menu=menu)
    assert icon.icon
    icon.run()


systray_p = Process(target=create_systray)


class OgLinuxOperations:

    def __init__(self):
        mp.set_start_method('spawn')
        systray_p.start()

    def _restartBrowser(self, url):
        raise NotImplementedError

    def poweroff(self):
        systray_p.terminate()
        os.system('systemctl poweroff')

    def reboot(self):
        systray_p.terminate()
        os.system('systemctl reboot')

    def shellrun(self, request, ogRest):
        raise NotImplementedError

    def session(self, request, ogRest):
        raise NotImplementedError

    def hardware(self, path, ogRest):
        raise NotImplementedError

    def setup(self, request, ogRest):
        raise NotImplementedError

    def image_restore(self, request, ogRest):
        raise NotImplementedError

    def image_create(self, path, request, ogRest):
        raise NotImplementedError

    def refresh(self, ogRest):
        return {"status": "LINUX"}

    def probe(self, ogRest):
        return {'status': 'LINUX' if ogRest.state != ThreadState.BUSY else 'BSY'}
