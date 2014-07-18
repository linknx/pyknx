#!/usr/bin/python3

# Copyright (C) 2014 Cyrille Defranoux
#
# This file is part of Pyknx.
#
# Pyknx is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pyknx is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pyknx. If not, see <http://www.gnu.org/licenses/>.
#
# For any question, feature requests or bug reports, feel free to contact me at:
# knx at aminate dot net

import sys
from pyknx import logger, linknx, configurator
import pyknx.testing.base
from pyknx.communicator import Communicator
import logging
import test
import os.path
import subprocess
import unittest
import time
import traceback
import tempfile
import inspect
import stat
import pwd, grp
import shutil

class PyknxWriteTestCase(pyknx.testing.base.WithLinknxTestCase):
	def setUp(self):
		pyknx.testing.base.WithLinknxTestCase.setUp(self)
		self.pyknxWritePyFile = os.path.join(self.pyknxScriptsDirectory, 'pyknxwrite.py')

	def testHelp(self):
		self.assertShellCommand([self.pyknxWritePyFile, '-h'], self.getResourceFullName('out'))

	def testWrite(self):
		object = self.linknx.getObject('Boolean')
		initialBoolValue = object.value

		newValue = initialBoolValue
		for i in range(2):
			newValue = not newValue
			self.assertShellCommand([self.pyknxWritePyFile, '-v', 'error', '-s', self.linknx.address[0], '-p', str(self.linknx.address[1]), 'Boolean', str(newValue)])
			self.assertEqual(object.value, newValue)

if __name__ == '__main__':
	unittest.main()
