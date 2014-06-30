#!/usr/bin/python3
# coding=utf-8

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
