#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

#!/usr/bin/env python3

import subprocess

# Run all tests in folder units.
subprocess.run('python3 -m unittest discover -s units -v', shell=True)
