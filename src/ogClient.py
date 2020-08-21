#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import errno
import select
import socket
import time
import email
import platform
from io import StringIO

from src.restRequest import *
from src.ogRest import *
from enum import Enum

class State(Enum):
	CONNECTING = 0
	RECEIVING = 1
	FORCE_DISCONNECTED = 2

class ogClient:
	OG_PATH = '/opt/opengnsys/'

	def __init__(self, config):
		self.CONFIG = config

		self.mode = self.CONFIG['opengnsys']['mode']
		if self.mode not in {'virtual', 'live'}:
			raise ValueError('Mode not supported.')

		if self.CONFIG['samba']['activate']:
			assert('user' in self.CONFIG['samba'])
			assert('pass' in self.CONFIG['samba'])

		self.ip = self.CONFIG['opengnsys']['ip']
		self.port = self.CONFIG['opengnsys']['port']
		self.ogrest = ogRest(self.CONFIG)

	def get_socket(self):
		return self.sock

	def get_state(self):
		return self.state

	def connect(self):
		print('connecting...')
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.state = State.CONNECTING
		self.data = ""
		self.trailer = False
		self.content_len = 0

		try:
			self.sock.connect((self.ip, self.port))
		except socket.error as err:
			if err.errno == errno.EINPROGRESS:
				return
			elif err.errno == errno.ECONNREFUSED:
				return

	def send(self, msg):
		self.sock.send(bytes(msg, 'utf-8'))
		return len(msg)

	def connect2(self):
		try:
			self.sock.connect((self.ip, self.port))
		except socket.error as err:
			if err.errno == errno.EISCONN:
				print('connected')
				self.state = State.RECEIVING
			else:
				time.sleep(1)
				print('connection refused, retrying...')
				self.state = State.CONNECTING
				self.sock.close()
				self.connect()

	def receive(self):
		try:
			data = self.sock.recv(1024).decode('utf-8')
		except socket.error as err:
			data = ''
			print('failed to received ' + str(err))

		if len(data) == 0:
			self.state = State.CONNECTING
			self.sock.close()
			self.connect()

		self.data = self.data + data
		request = restRequest()

		if not self.trailer:
			if self.data.find("\r\n") > 0:
				# https://stackoverflow.com/questions/4685217/parse-raw-http-headers
				request_line, headers_alone = self.data.split('\n', 1)
				headers = email.message_from_file(StringIO(headers_alone))

				if 'content-length' in headers.keys():
					self.content_len = int(headers['content-length'])

				self.trailer = True

		if self.trailer and len(self.data) >= self.content_len:
			request.parser(self.data)
			self.ogrest.process_request(request, self)

			# Cleanup state information from request
			self.data = ""
			self.content_len = 0
			self.trailer = False

	def disconnect(self):
		self.state = State.FORCE_DISCONNECTED
		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()

	def run(self):
		while 1:
			sock = self.get_socket()
			state = self.get_state()

			if state == State.CONNECTING:
				readset = [ sock ]
				writeset = [ sock ]
			elif state == State.FORCE_DISCONNECTED:
				return 0
			else:
				readset = [ sock ]
				writeset = [ ]

			readable, writable, exception = select.select(readset, writeset, [ ])
			if state == State.CONNECTING and sock in writable:
				self.connect2()
			elif state == State.RECEIVING and sock in readable:
				self.receive()
			else:
				print('wrong state, not ever happen!' + str(state))
