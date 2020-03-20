#
# Copyright (C) 2020 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, version 3.
#

import configparser

class ogConfig:
	OG_PATH = '/opt/opengnsys/'

	def __init__(self):
		self.parser = configparser.ConfigParser()

	def parser_file(self, path):
		self.parser.read(path)
		if len(self.parser.sections()) == 0:
			return False

		return True

	def get_sections(self):
		return self.parser.sections()

	def get_contains_section(self, section):
		return section in self.parser

	def get_value_section(self, section, key):
		if (not self.get_contains_section(section)):
			return ''

		return self.parser[section][key]
