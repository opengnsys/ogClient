#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

from src.ogClient import *
from src.ogConfig import *
from signal import signal, SIGPIPE, SIG_DFL

def main():
	signal(SIGPIPE, SIG_DFL)
	ogconfig = ogConfig()
	if (not ogconfig.parserFile('cfg/ogagent.cfg')):
		print ('Error: Parsing configuration file')
		return 0

	ip = ogconfig.getValueSection('opengnsys', 'ip')
	port = ogconfig.getValueSection('opengnsys', 'port')

	client = ogClient(ip, int(port))
	client.connect()
	client.run()

if __name__ == "__main__":
	main()
