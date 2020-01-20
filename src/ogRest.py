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

from src.restRequest import *

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
	def __init__(self, response, jsonResp=None):
		self.msg = ''
		if response == ogResponses.BAD_REQUEST:
			self.msg = 'HTTP/1.0 400 Bad Request'
		elif response == ogResponses.IN_PROGRESS:
			self.msg = 'HTTP/1.0 202 Accepted'
		elif response == ogResponses.OK:
			self.msg = 'HTTP/1.0 200 OK'
		elif response == ogResponses.INTERNAL_ERR:
			self.msg = 'HTTP/1.0 500 Internal Server Error'
		elif response == ogResponses.UNAUTHORIZED:
			self.msg = 'HTTP/1.0 401 Unauthorized'
		else:
			return self.msg

		self.msg += '\r\n'

		if jsonResp:
			self.msg += 'Content-Length:' + str(len(jsonResp.dumpMsg()))
			self.msg += '\r\nContent-Type:application/json'
			self.msg += '\r\n\r\n' + jsonResp.dumpMsg()
		else:
			self.msg += '\r\n'


	def get(self):
		return self.msg

class ogThread():
	def execcmd(client, request, ogRest):
		if not request.getrun():
			response = restResponse(ogResponses.BAD_REQUEST)
			client.send(response.get())
			return

		try:
			shellout = ogOperations.execCMD(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		if request.getEcho():
			jsonResp = jsonResponse()
			jsonResp.addElement('out', shellout)
			response = restResponse(ogResponses.OK, jsonResp)
			client.send(response.get())
		else:
			response = restResponse(ogResponses.OK)
			client.send(response.get())

	def poweroff():
		time.sleep(2)
		ogOperations.poweroff()

	def reboot():
		ogOperations.reboot()

	def session(client, request, ogRest):
		try:
			ogOperations.session(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		response = restResponse(ogResponses.OK)
		client.send(response.get())

	def software(client, request, path, ogRest):
		try:
			ogOperations.software(request, path, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		jsonResp = jsonResponse()
		jsonResp.addElement('disk', request.getDisk())
		jsonResp.addElement('partition', request.getPartition())

		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('software', lines[0])

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

	def hardware(client, path, ogRest):
		try:
			ogOperations.hardware(path, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		jsonResp = jsonResponse()
		f = open(path, "r")
		text = f.read()
		f.close()
		jsonResp.addElement('hardware', text)

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

	def setup(client, request, ogRest):
		listconfig = []

		try:
			listconfig = ogOperations.setup(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		jsonResp = jsonResponse()
		jsonResp.addElement('disk', request.getDisk())
		jsonResp.addElement('cache', request.getCache())
		jsonResp.addElement('cache_size', request.getCacheSize())
		jsonResp.addElement('partition_setup', listconfig)

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

	def image_restore(client, request, ogRest):
		try:
			ogOperations.image_restore(request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

	def image_create(client, path, request, ogRest):
		try:
			ogOperations.image_create(path, request, ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		jsonResp = jsonResponse()
		jsonResp.addElement('disk', request.getDisk())
		jsonResp.addElement('partition', request.getPartition())
		jsonResp.addElement('code', request.getCode())
		jsonResp.addElement('id', request.getId())
		jsonResp.addElement('name', request.getName())
		jsonResp.addElement('repository', request.getRepo())
		f = open(path, "r")
		lines = f.readlines()
		f.close()
		jsonResp.addElement('software', lines[0])

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

	def refresh(client, ogRest):
		try:
			out = ogOperations.refresh(ogRest)
		except ValueError as err:
			response = restResponse(ogResponses.INTERNAL_ERR)
			client.send(response.get())
			return

		jsonResp = jsonResponse()
		jsonResp.addElement('disk', out[0])
		jsonResp.addElement('partition_setup', out[1])

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

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

	def processOperation(self, request, client):
		op = request.getRequestOP()
		URI = request.getURI()

		if (not "stop" in URI and not self.proc == None and self.proc.poll() == None):
			response = restResponse(ogResponses.UNAUTHORIZED)
			client.send(response.get())
			return

		if ("GET" in op):
			if "hardware" in URI:
				self.process_hardware(client)
			elif ("run/schedule" in URI):
				self.process_schedule(client)
			else:
				response = restResponse(ogResponses.BAD_REQUEST)
				client.send(response.get())
		elif ("POST" in op):
			if ("poweroff" in URI):
				self.process_poweroff(client)
			elif "probe" in URI:
				self.process_probe(client)
			elif ("reboot" in URI):
				self.process_reboot(client)
			elif ("shell/run" in URI):
				self.process_shellrun(client, request)
			elif ("session" in URI):
				self.process_session(client, request)
			elif ("software" in URI):
				self.process_software(client, request)
			elif ("setup" in URI):
				self.process_setup(client, request)
			elif ("image/restore" in URI):
				self.process_imagerestore(client, request)
			elif ("stop" in URI):
				self.process_stop(client)
			elif ("image/create" in URI):
				self.process_imagecreate(client, request)
			elif ("refresh" in URI):
				self.process_refresh(client)
			else:
				response = restResponse(ogResponses.BAD_REQUEST)
				client.send(response.get())
		else:
			response = restResponse(ogResponses.BAD_REQUEST)
			client.send(response.get())

		return 0

	def process_reboot(self, client):
		response = restResponse(ogResponses.IN_PROGRESS)
		client.send(response.get())

		client.disconnect()
		threading.Thread(target=ogThread.reboot).start()

	def process_poweroff(self, client):
		response = restResponse(ogResponses.IN_PROGRESS)
		client.send(response.get())

		client.disconnect()
		threading.Thread(target=ogThread.poweroff).start()

	def process_probe(self, client):
		jsonResp = jsonResponse()
		jsonResp.addElement('status', 'OPG')

		response = restResponse(ogResponses.OK, jsonResp)
		client.send(response.get())

	def process_shellrun(self, client, request):
		threading.Thread(target=ogThread.execcmd, args=(client, request, self,)).start()

	def process_session(self, client, request):
		threading.Thread(target=ogThread.session, args=(client, request, self,)).start()

	def process_software(self, client, request):
		path = '/tmp/CSft-' + client.ip + '-' + request.getPartition()
		threading.Thread(target=ogThread.software, args=(client, request, path, self,)).start()

	def process_hardware(self, client):
		path = '/tmp/Chrd-' + client.ip
		threading.Thread(target=ogThread.hardware, args=(client, path, self,)).start()

	def process_schedule(self, client):
		response = restResponse(ogResponses.OK)
		client.send(response.get())

	def process_setup(self, client, request):
		threading.Thread(target=ogThread.setup, args=(client, request, self,)).start()

	def process_imagerestore(self, client, request):
		threading.Thread(target=ogThread.image_restore, args=(client, request, self,)).start()

	def process_stop(self, client):
		client.disconnect()
		if self.proc == None:
			return

		if self.proc.poll() == None:
			os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
			self.terminated = True
			sys.exit(0)

	def process_imagecreate(self, client, request):
		path = '/tmp/CSft-' + client.ip + '-' + request.getPartition()
		threading.Thread(target=ogThread.image_create, args=(client, path, request, self,)).start()

	def process_refresh(self, client):
		threading.Thread(target=ogThread.refresh, args=(client, self,)).start()
