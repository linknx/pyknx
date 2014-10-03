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
from pyknx import logger, linknx, configurator, communicator, Version
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

class VersionTestCase(base.TestCaseBase):
    def testVersion(self):
        def checkGreaterThan(first, second):
            self.assertTrue(first > second)
            self.assertTrue(first >= second)
            self.assertTrue(first != second)
            self.assertFalse(first == second)
            self.assertFalse(first < second)
            self.assertFalse(first <= second)
        checkGreaterThan(Version(1,2,3), Version(1,2,2))
        checkGreaterThan(Version(1,2,3), Version(1,1,3))
        checkGreaterThan(Version(1,2,3), Version(0,2,3))
        checkGreaterThan(Version(1,2,3), Version(1,2,3,'a',1))
        checkGreaterThan(Version(1,2,3), Version(1,2,3,'a',1))
        checkGreaterThan(Version(1,2,3,'a',2), Version(1,2,3,'a',1))
        checkGreaterThan(Version(1,2,3,'b',2), Version(1,2,3,'b',1))
        checkGreaterThan(Version(1,2,3,'b',2), Version(1,2,3,'a',3))
        checkGreaterThan(Version(1,3,0,'b',1), Version(1,2,3))

        self.assertTrue(Version(1,2,0).isRelease)
        self.assertFalse(Version(1,2,0,'a',1).isRelease)
        self.assertFalse(Version(1,2,0,'b',1).isRelease)

if __name__ == '__main__':
    unittest.main()
