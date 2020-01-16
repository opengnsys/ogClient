#!/usr/bin/env python3

import subprocess

# Run all tests in folder units.
subprocess.run('python3 -m unittest discover -s units -v', shell=True)
