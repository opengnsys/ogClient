#!/bin/python3

#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import json
import subprocess
from src.ogClient import *
from src.ogConfig import *
from signal import signal, SIGPIPE, SIG_DFL

def main():
	signal(SIGPIPE, SIG_DFL)
	config_path = f'{ogConfig.OG_PATH}ogclient/cfg/ogclient.json'
	try:
		with open(config_path, 'r') as f:
			CONFIG = json.load(f)
	except:
		print('Error: Parsing configuration file')
		return 0

	MODE = CONFIG['opengnsys']['mode']
	URL = CONFIG['opengnsys']['url']
	if MODE == 'linux':
		proc = subprocess.Popen(["browser", "-qws", URL])

	client = ogClient(config=CONFIG)
	client.connect()
	client.run()

if __name__ == "__main__":
	main()
