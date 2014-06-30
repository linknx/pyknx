#!/usr/bin/python3
# coding=utf-8

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

class PyknxClientTestCase(pyknx.testing.base.WithLinknxTestCase):
	def setUp(self):
		pyknx.testing.base.WithLinknxTestCase.setUp(self)
		self.pyknxClientPyFile = os.path.join(self.pyknxScriptsDirectory, 'pyknxclient.py')

	def testHelp(self):
		self.assertShellCommand([self.pyknxClientPyFile, '-h'], self.getResourceFullName('out'))

	def testRead(self):
		self.assertShellCommand([self.pyknxClientPyFile, '-v', 'error', '-s', self.linknx.address[0], '-p', str(self.linknx.address[1]), 'read', 'Boolean'], self.getResourceFullName('outFalse'))
		self.assertShellCommand([self.pyknxClientPyFile, '-v', 'error', '-s', self.linknx.address[0], '-p', str(self.linknx.address[1]),'--value-only', 'read', 'Boolean'], self.getResourceFullName('outvalueonly'))
		for v in (True, False):
			self.linknx.getObject('Boolean').value = v
			expectedStdOut = self.getResourceFullName('outTrue' if v else 'outFalse')
			for value in ('1', 'true', 'True', 'TRUE', 'on', 'ON', 'yes', 'YES'):
				self.assertShellCommand([self.pyknxClientPyFile, '-s', self.linknx.address[0], '-p', str(self.linknx.address[1]), '-v', 'error', '--expected-value', value, 'read', 'Boolean'], expectedReturnCode=0 if v else 100, expectedStdOut=expectedStdOut)
			for value in ('0', 'false', 'False', 'FALSE', 'off', 'OFF', 'no', 'NO'):
				self.assertShellCommand([self.pyknxClientPyFile, '-s', self.linknx.address[0], '-p', str(self.linknx.address[1]), '-v', 'error', '--expected-value', value, 'read', 'Boolean'], expectedReturnCode=100 if v else 0, expectedStdOut=expectedStdOut)

	# def testWrite(self):


if __name__ == '__main__':
	unittest.main()
