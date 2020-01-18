#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import email
from io import StringIO
import json

class HTTPParser:
	def __init__(self):
		self.requestLine = None
		self.headersAlone = None
		self.headers = None
		self.host = None
		self.contentType = None
		self.contentLen = None
		self.operation = None
		self.URI = None
		self.run = None
		self.partition = None
		self.disk = None
		self.cache = None
		self.cache_size = None
		self.partition_setup = None
		self.name = None
		self.repo = None
		self.type = None
		self.profile = None
		self.id = None
		self.echo = None
		self.code = None

	def parser(self,data):
		self.requestLine, self.headersAlone = data.split('\n', 1)
		self.headers = email.message_from_file(StringIO(self.headersAlone))

		if 'Host' in self.headers.keys():
			self.host = self.headers['Host']

		if 'Content-Type' in self.headers.keys():
			self.contentType = self.headers['Content-Type']

		if 'Content-Length' in self.headers.keys():
			self.contentLen = int(self.headers['Content-Length'])

		if (not self.requestLine == None or not self.requestLine == ''):
			self.operation = self.requestLine.split('/', 1)[0]
			self.URI = self.requestLine.split('/', 1)[1]

		if not self.contentLen == 0:
			msgs = self.headersAlone.rstrip().split('\n')
			cmd = msgs[len(msgs) - 1]
			try:
				json_param = json.loads(cmd)
			except ValueError as e:
				print ("Error: Json message incomplete")
				return

			if "run" in cmd:
				self.run = json_param["run"]
				try:
					self.echo = json_param["echo"]
				except:
					pass

			if "disk" in cmd:
				self.disk = json_param["disk"]

			if "partition" in cmd:
				if not "partition_setup" in cmd:
					self.partition = json_param["partition"]

			if "cache" in cmd:
				self.cache = json_param["cache"]

			if "cache_size" in cmd:
				self.cache_size = json_param["cache_size"]

			if "partition_setup" in cmd:
				self.partition_setup = json_param["partition_setup"]

			if "name" in cmd:
				self.name = json_param["name"]

			if "repository" in cmd:
				self.repo = json_param["repository"]

			if "type" in cmd:
				self.type = json_param["type"]

			if "profile" in cmd:
				self.profile = json_param["profile"]

			if "id" in cmd:
				self.id = json_param["id"]

			if "code" in cmd:
				self.code = json_param["code"]

	def getHeaderLine(self):
		return self.headersAlone

	def getRequestLine(self):
		return self.requestLine

	def getHeaderParsed(self):
		return self.headers

	def getHost(self):
		return self.host

	def getContentType(self):
		return self.contentType

	def getContentLen(self):
		return self.contentLen

	def getRequestOP(self):
		return self.operation

	def getURI(self):
		return self.URI

	def getrun(self):
		return self.run

	def getDisk(self):
		return self.disk

	def getPartition(self):
		return self.partition

	def getCache(self):
		return self.cache

	def getCacheSize(self):
		return self.cache_size

	def getPartitionSetup(self):
		return self.partition_setup

	def getName(self):
		return self.name

	def getRepo(self):
		return self.repo

	def getType(self):
		return self.type

	def getProfile(self):
		return self.profile

	def getId(self):
		return self.id

	def getEcho(self):
		return self.echo

	def getCode(self):
		return self.code
