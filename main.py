#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import subprocess
from src.ogClient import *
from src.ogConfig import *
from signal import signal, SIGPIPE, SIG_DFL

def main():
	signal(SIGPIPE, SIG_DFL)
	ogconfig = ogConfig()
	config_path = f'{ogConfig.OG_PATH}ogClient/cfg/ogclient.cfg'
	if (not ogconfig.parser_file(config_path)):
		print ('Error: Parsing configuration file')
		return 0

	ip = ogconfig.get_value_section('opengnsys', 'ip')
	port = ogconfig.get_value_section('opengnsys', 'port')
	url = ogconfig.get_value_section('opengnsys', 'url')

	proc = subprocess.Popen(["browser", "-qws", url])

	client = ogClient(ip, int(port))
	client.connect()
	client.run()

if __name__ == "__main__":
	main()
