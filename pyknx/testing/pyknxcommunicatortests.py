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
sys.path.append('../')
from pyknx import logger, linknx, configurator, communicator
from pyknx.testing import base
import logging
import os.path
import subprocess
import unittest
import time
import traceback
import inspect
import stat
import pwd, grp
import shutil

class PyknxCommunicatorTestCase(base.WithLinknxTestCase):
	def setUp(self):
		base.WithLinknxTestCase.setUp(self, communicatorAddr=None)
		self.pyknxCommunicatorPyFile= os.path.join(self.pyknxScriptsDirectory, 'pyknxcommunicator.py')

	def testNoOption(self):
		stderr = self.getResourceFullName('err')
		self.assertShellCommand([self.pyknxCommunicatorPyFile], expectedStdErr=stderr)

	def testBadOption(self):
		stderrShort = self.getResourceFullName('err.short')
		stderrLong = self.getResourceFullName('err.long')
		self.assertShellCommand([self.pyknxCommunicatorPyFile, '-b'], expectedStdErr=stderrShort)
		self.assertShellCommand([self.pyknxCommunicatorPyFile, '--bad-option'], expectedStdErr=stderrLong)

	def testHelp(self):
		stdout = self.getResourceFullName('out')
		self.assertShellCommand([self.pyknxCommunicatorPyFile, '-h'], stdout)
		self.assertShellCommand([self.pyknxCommunicatorPyFile, '--help'], stdout)

if __name__ == '__main__':
	unittest.main()
