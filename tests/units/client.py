#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

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
