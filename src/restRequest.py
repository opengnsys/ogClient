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

class restRequest:
	def __init__(self):
		self.request_line = None
		self.headers_alone = None
		self.headers = None
		self.host = None
		self.content_type = None
		self.content_len = None
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
		self.request_line, self.headers_alone = data.split('\n', 1)
		self.headers = email.message_from_file(StringIO(self.headers_alone))

		if 'Host' in self.headers.keys():
			self.host = self.headers['Host']

		if 'Content-Type' in self.headers.keys():
			self.content_type = self.headers['Content-Type']

		if 'Content-Length' in self.headers.keys():
			self.content_len = int(self.headers['Content-Length'])

		if (not self.request_line == None or not self.request_line == ''):
			self.method = self.request_line.split('/', 1)[0]
			self.URI = self.request_line.split('/', 1)[1]

		if not self.content_len == 0:
			msgs = self.headers_alone.rstrip().split('\n')
			body = msgs[len(msgs) - 1]
			try:
				json_param = json.loads(body)
			except ValueError as e:
				print ("Error: Json message incomplete")
				return

			if "run" in json_param:
				self.run = json_param["run"]
				try:
					self.echo = json_param["echo"]
				except:
					pass

			if "disk" in json_param:
				self.disk = json_param["disk"]

			if "partition" in json_param:
				self.partition = json_param["partition"]

			if "cache" in json_param:
				self.cache = json_param["cache"]

			if "cache_size" in json_param:
				self.cache_size = json_param["cache_size"]

			if "partition_setup" in json_param:
				self.partition_setup = json_param["partition_setup"]

			if "name" in json_param:
				self.name = json_param["name"]

			if "repository" in json_param:
				self.repo = json_param["repository"]

			if "type" in json_param:
				self.type = json_param["type"]

			if "profile" in json_param:
				self.profile = json_param["profile"]

			if "id" in json_param:
				self.id = json_param["id"]

			if "code" in json_param:
				self.code = json_param["code"]

	def get_method(self):
		return self.method

	def get_uri(self):
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
