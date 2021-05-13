#
# Copyright (C) 2020-2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import subprocess
import os

class Client():

    def __init__(self):
        self.null = open(os.devnull, 'wb')
        self.proc = subprocess.Popen(['python3', 'ogclient'],
                                     cwd='../',
                                     stdout=self.null,
                                     stderr=self.null)

    def stop(self):
        self.proc.terminate()
        self.proc.kill()
        self.proc.wait()
        self.null.close()
