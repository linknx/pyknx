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

class PyknxConfTestCase(pyknx.testing.base.TestCaseBase):
	def setUp(self):
		pyknx.testing.base.TestCaseBase.setUp(self)
		self.pyknxConfPyFile = os.path.join(self.pyknxScriptsDirectory, 'pyknxconf.py')

	def testHelp(self):
		self.assertShellCommand([self.pyknxConfPyFile, '-h'], self.getResourceFullName('out'))

	def testGeneratedConfiguration(self):
		# Input from file, output to stdout.
		self.assertShellCommand([self.pyknxConfPyFile, '-v', 'error', '-i', 'linknx_test_conf.xml'], self.getResourceFullName('out'))

		# Input from file, output to file.
		generatedFile = self.getOutputFullName('output.xml')
		self.assertShellCommand([self.pyknxConfPyFile, '-o', generatedFile, '-i', 'linknx_test_conf.xml'])
		self.assertFilesAreEqual(generatedFile, self.getResourceFullName('out'))

		# Input from stdin, output to stdout.
		with open('linknx_test_conf.xml', 'r') as input:
			self.assertShellCommand([self.pyknxConfPyFile, '-v', 'error'], self.getResourceFullName('out2'), stdin=input)

		# Input from stdin, output to file.
		with open('linknx_test_conf.xml', 'r') as input:
			self.assertShellCommand([self.pyknxConfPyFile, '-o', generatedFile], stdin=input)
		self.assertFilesAreEqual(generatedFile, self.getResourceFullName('out2'))

if __name__ == '__main__':
	unittest.main()
