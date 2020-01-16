#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import configparser

class ogConfig:
	def __init__(self):
		self.parser = configparser.ConfigParser()

	def parserFile(self, path):
		self.parser.read(path)
		if len(self.parser.sections()) == 0:
			return False

		return True

	def getSections(self):
		return self.parser.sections()

	def getContainsSection(self, section):
		return section in self.parser

	def getValueSection(self, section, key):
		if (not self.getContainsSection(section)):
			return ''

		return self.parser[section][key]
