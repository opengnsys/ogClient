#
# Copyright (C) 2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import os
import subprocess
from subprocess import CalledProcessError

from src.ogRest import ThreadState

class OgLinuxOperations:

    def _restartBrowser(self, url):
        raise NotImplementedError

    def poweroff(self):
        os.system('systemctl poweroff')

    def reboot(self):
        os.system('systemctl reboot')

    def shellrun(self, request, ogRest):
        cmd = request.getrun()
        try:
            result = subprocess.run(cmd,
                                    shell=True,
                                    stdin=subprocess.DEVNULL,
                                    capture_output=True,
                                    text=True,
                                    check=True)
        except CalledProcessError as error:
            if error.stderr:
                return error.stderr
            if error.stdout:
                return error.stdout
            return "{Non zero exit code and empty output}"
        return result.stdout

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
