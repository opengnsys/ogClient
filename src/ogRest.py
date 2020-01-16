#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import threading
import platform
import time
from enum import Enum
import json
import queue
import sys
import os
import signal

from src.HTTPParser import *

if platform.system() == 'Linux':
	from src.linux import ogOperations

class jsonResponse():
	def __init__(self):
		self.jsontree = {}

	def addElement(self, key, value):
		self.jsontree[key] = value

	def dumpMsg(self):
		return json.dumps(self.jsontree)

class restResponse():
	def getResponse(response, jsonResp=None):
		msg = ''
		if response == ogResponses.BAD_REQUEST:
			msg = 'HTTP/1.0 400 Bad Request'
		elif response == ogResponses.IN_PROGRESS:
			msg = 'HTTP/1.0 202 Accepted'
		elif response == ogResponses.OK:
			msg = 'HTTP/1.0 200 OK'
		elif response == ogResponses.INTERNAL_ERR:
			msg = 'HTTP/1.0 500 Internal Server Error'
		elif response == ogResponses.UNAUTHORIZED:
			msg = 'HTTP/1.0 401 Unauthorized'
		else:
			return msg

		msg += '\r\n'

		if jsonResp:
			msg += 'Content-Length:' + str(len(jsonResp.dumpMsg()))
			msg += '\r\nContent-Type:application/json'
			msg += '\r\n\r\n' + jsonResp.dumpMsg()
		else:
			msg += '\r\n'

		return msg

class ogThread():
	# Executing cmd thread
	def execcmd(client, httpparser, ogRest):
		if httpparser.getCMD() == None:
			client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
			return

		try:
			shellout = ogOperations.execCMD(httpparser, ogRest)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
			return

		if httpparser.getEcho():
			jsonResp = jsonResponse()
			jsonResp.addElement('out', shellout)
			client.send(restResponse.getResponse(ogResponses.OK, jsonResp))
		else:
			client.send(restResponse.getResponse(ogResponses.OK))

	# Powering off thread
	def poweroff():
		time.sleep(2)
		ogOperations.poweroff()

	# Rebooting thread
	def reboot():
		ogOperations.reboot()

	# Process session
	def procsession(client, httpparser, ogRest):
		try:
			ogOperations.procsession(httpparser, ogRest)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		client.send(restResponse.getResponse(ogResponses.OK))

	# Process software
	def procsoftware(client, httpparser, path, ogRest):
		try:
			ogOperations.procsoftware(httpparser, path, ogRest)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		jsonResp = jsonResponse()
		jsonResp.addElement('disk', httpparser.getDisk())
		jsonResp.addElement('partition', httpparser.getPartition())

		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('software', lines[0])

		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	# Process hardware
	def prochardware(client, path, ogRest):
		try:
			ogOperations.prochardware(path, ogRest)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		jsonResp = jsonResponse()
		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('hardware', lines[0])
		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	# Process setup
	def procsetup(client, httpparser, ogRest):
		jsonResp = jsonResponse()
		jsonResp.addElement('disk', httpparser.getDisk())
		jsonResp.addElement('cache', httpparser.getCache())
		jsonResp.addElement('cache_size', httpparser.getCacheSize())
		listconfig = ogOperations.procsetup(httpparser, ogRest)
		jsonResp.addElement('partition_setup', listconfig)
		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	# Process image restore
	def procirestore(client, httpparser, ogRest):
		try:
			ogOperations.procirestore(httpparser, ogRest)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		client.send(restResponse.getResponse(ogResponses.OK))

	# Process image create
	def procicreate(client, path, httpparser, ogRest):
		try:
			ogOperations.procicreate(path, httpparser, ogRest)
		except ValueError as err:
			client.send(restResponse.getResponse(ogResponses.INTERNAL_ERR))
			return

		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('software', lines[0])
		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

class ogResponses(Enum):
	BAD_REQUEST=0
	IN_PROGRESS=1
	OK=2
	INTERNAL_ERR=3
	UNAUTHORIZED=4

class ogRest():
	def __init__(self):
		self.proc = None
		self.terminated = False

	def processOperation(self, httpparser, client):
		op = httpparser.getRequestOP()
		URI = httpparser.getURI()

		if (not "stop" in URI and not self.proc == None and self.proc.poll() == None):
			client.send(restResponse.getResponse(ogResponses.UNAUTHORIZED))
			return

		if ("GET" in op):
			if "hardware" in URI:
				self.process_hardware(client)
			elif ("run/schedule" in URI):
				self.process_schedule(client)
			else:
				client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
		elif ("POST" in op):
			if ("poweroff" in URI):
				self.process_poweroff(client)
			elif "probe" in URI:
				self.process_probe(client)
			elif ("reboot" in URI):
				self.process_reboot(client)
			elif ("shell/run" in URI):
				self.process_shellrun(client, httpparser)
			elif ("session" in URI):
				self.process_session(client, httpparser)
			elif ("software" in URI):
				self.process_software(client, httpparser)
			elif ("setup" in URI):
				self.process_setup(client, httpparser)
			elif ("image/restore" in URI):
				self.process_irestore(client, httpparser)
			elif ("stop" in URI):
				self.process_stop(client)
			elif ("image/create" in URI):
				self.process_icreate(client, httpparser)
			else:
				client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))
		else:
			client.send(restResponse.getResponse(ogResponses.BAD_REQUEST))

		return 0

	def process_reboot(self, client):
		client.send(restResponse.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=ogThread.reboot).start()

	def process_poweroff(self, client):
		client.send(restResponse.getResponse(ogResponses.IN_PROGRESS))
		client.disconnect()
		threading.Thread(target=ogThread.poweroff).start()

	def process_probe(self, client):
		jsonResp = jsonResponse()
		jsonResp.addElement('status', 'OPG')
		client.send(restResponse.getResponse(ogResponses.OK, jsonResp))

	def process_shellrun(self, client, httpparser):
		threading.Thread(target=ogThread.execcmd, args=(client, httpparser, self,)).start()

	def process_session(self, client, httpparser):
		threading.Thread(target=ogThread.procsession, args=(client, httpparser, self,)).start()

	def process_software(self, client, httpparser):
		path = '/tmp/CSft-' + client.ip + '-' + httpparser.getPartition()
		threading.Thread(target=ogThread.procsoftware, args=(client, httpparser, path, self,)).start()

	def process_hardware(self, client):
		path = '/tmp/Chrd-' + client.ip
		threading.Thread(target=ogThread.prochardware, args=(client, path, self,)).start()

	def process_schedule(self, client):
		client.send(restResponse.getResponse(ogResponses.OK))

	def process_setup(self, client, httpparser):
		threading.Thread(target=ogThread.procsetup, args=(client, httpparser, self,)).start()

	def process_irestore(self, client, httpparser):
		threading.Thread(target=ogThread.procirestore, args=(client, httpparser, self,)).start()

	def process_stop(self, client):
		client.disconnect()
		if self.proc == None:
			return

		if self.proc.poll() == None:
			os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
			self.terminated = True
			sys.exit(0)

	def process_icreate(self, client, httpparser):
		path = '/tmp/CSft-' + client.ip + '-' + httpparser.getPartition()
		threading.Thread(target=ogThread.procicreate, args=(client, path, httpparser, self,)).start()
