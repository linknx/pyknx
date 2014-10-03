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

class PyknxTestCase(base.WithLinknxTestCase):
    # COMMUNICATOR_ADDRESS = ('127.0.0.1', 1031)

    def mockForTestMultipleConnections(self, context):
        logger.reportDebug('Mock called with objectId={0}'.format(context.objectId))
        self.callbackCalledFor.append(context.object)
        while self.blockCallback:
            time.sleep(0.5)
        logger.reportDebug('Mock ended for objectId={0}'.format(context.objectId))

        # Make sure next callback is blocked!
        self.blockCallback = True

    # def testGAddressesUniqueness(self):
        # GAs={}
        # for objId, obj in self.linknx.objectConfig.items():
            # self.assertIsNot(obj.gad, '', 'No group address defined for {0}'.format(objId))
            # self.assertNotIn(obj.gad, GAs, 'Group Address {0} is assigned to at least two objects.'.format(obj.gad))
            # GAs[obj.gad]=obj
# 
    def testMultipleConnections(self):
        """ Checks that communicator can handle several connections at once (with a queue of connections when a connection is being treated). """
        # Set state to a known one.
        booleanObject = self.linknx.getObject('Boolean')
        floatObject = self.linknx.getObject('Float16')
        booleanObject.value = False
        floatObject.value = 0.0
        self.waitDuring(2, 'Initializing...')

        # Redirect some events to be able to block them.
        self.callbackCalledFor = []
        try:
            self.blockCallback = True

            with self.patchUserModule({'onBooleanChanged' : self.mockForTestMultipleConnections, 'onFloatChanged' : self.mockForTestMultipleConnections}):

                # Change an object.
                booleanObject.value = True

                # Wait for callback.
                while not self.callbackCalledFor:
                    logger.reportDebug('Waiting for first callback...')
                    time.sleep(1)
                self.assertEqual(self.callbackCalledFor, [booleanObject])
                self.assertTrue(booleanObject.value)

                # Chain with second callback while first is blocked.
                floatObject.value = 1.0

                # Wait a few seconds, callback should not be called now (since it is not
                # reentrant).
                self.waitDuring(5, 'Checking that second callback is not called until first callback is released.', [lambda: self.assertEqual(self.callbackCalledFor, [booleanObject])])

                # Release callback.
                self.blockCallback = False

                # Wait for second callback.
                self.waitDuring(3, 'Waiting for second callback...')
                self.assertEqual(self.callbackCalledFor, [booleanObject, floatObject])

        finally:
            # Release all threads in case test went wrong.
            self.blockCallback = False

    def testObjectValueTypes(self):
        def testValues(objectId, values):
            logger.reportInfo('Testing {0} with values {1}'.format(objectId, values))
            for value in values:
                obj = self.linknx.getObject(objectId)
                assignedValue = value if not isinstance(value, tuple) else value[0]
                readValue = value if not isinstance(value, tuple) else value[1]
                obj.value = assignedValue
                self.assertEqual(obj.value, readValue)

        testValues('Boolean', (False, True))
        testValues('Unsigned Byte', range(256))
        testValues('Scaling Unsigned Byte', [0, (0.393, 0.392), (5.89, 5.88), (98.1, 98), 100])
        testValues('Angle Unsigned Byte', [0, (1.407, 1.406), (112.501, 112.5), (358.594, 358.6), (360, 0)])
        testValues('Byte', range(-128, 128))
        testValues('Unsigned Int16', (0, 10000, 65535))
        testValues('Int16', (-32768, -10000, 0, 10000, 32767))
        testValues('Float16', (0.0, 10, -10, 1234.56, -1234.56))
        testValues('Unsigned Int32', (0, 10000000, 4294967295))
        testValues('Int32', (-2147483647, -100000000, 0, 10000000, 2147483647))
        testValues('Float32', (0.0, 10, -10, 1234.567, -1234.567))
        testValues('Ascii String14', ('abcdefghijklmn', 'opqrstuvwxyzab', 'ABCDEF HIJKLMN', 'OPQRSTUVWX ZAB'))
        testValues('Extended Ascii String14', ('àbcdéfghîjklmn', 'ôpqrstùvwxyzab', 'ÀBCDÉFGHÎJKLMN', 'ÔPQRSTÙVWXYZAB'))
        testValues('String', ('àbcdéfghîjklmn', 'ôpqrstùvwxyzab', 'ÀBCDÉFGHÎJKLMN', 'ÔPQRSTÙVWXYZAB'))
        testValues('Int64', (-2147483647, -10000000, 0, 100000000, 2147483647))
        testValues('Latin1 Char', ('b', 'à', 'é', '1', '%', '&'))

    def testEmailServerAddress(self):
        self.assertEqual(self.linknx.emailServerInfo, ('emailprovider.com', 25, 'linknx@foo.com'))

if __name__ == '__main__':
    unittest.main()
