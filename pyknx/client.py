#!/usr/bin/python3

# Copyright (C) 2012-2014 Cyrille Defranoux
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

"""
Module that implements functionality common to all client scripts (pyknxread, pyknxwrite, pyknxexecute).
"""

import sys
import argparse
import traceback
import logging
from xml.dom.minidom import parseString
from threading import *
from pyknx import logger
from pyknx.linknx import *

def handleRequest(requestType, doc):
    logger.initLogger(None, logging.INFO, usesDetailedLogging=False)

    parser = argparse.ArgumentParser(description=doc)
    parser.add_argument('-s', '--server', dest='host', help='Hostname of the machine running the linknx daemon. Default is localhost.', default='localhost')
    parser.add_argument('-p', '--port', dest='port', help='Port linknx listens on. Default is 1028.', default=1028)
    if requestType == 'read':
        parser.add_argument('objectIds', help='ID represents the identifier of the object to read.', metavar='ID', nargs='+')
        parser.add_argument('-R', '--regex', action='store_true', help='ID in the "object" argument is interpreted as a regex and used to find objects to read. The pattern must comply with the \'re\' python module.')
        parser.add_argument('--value-only', action='store_true', help='Output the value of the queried object but do not prefix it with the object\'s id.')
        parser.add_argument('--expected-value', help='Expected value of the object. This script will exit with a non-zero return code if the value is not the expected one. This is useful when using this script in a "if" test of a shell script.')
    elif requestType == 'write':
        parser.add_argument('object', help='ID represents the identifier of the object to write to.', metavar='ID')
        parser.add_argument('value', help='Assigns VALUE to the object identified by ID.', metavar='VALUE')
    elif requestType == 'execute':
        parser.add_argument('--action', help='use the ACTION string as the XML representation of the action to execute rather than reading it from standard input.', metavar='ACTION')
    else:
        raise Exception('Unsupported request type "{0}".'.format(requestType))
    parser.add_argument('-v', '--verbose', dest='verbosityLevel', help='Set verbosity level. Default is "error".', metavar='LEVEL', choices=[l.lower() for l in logger.getLevelsToString()], default='error')
    args = parser.parse_args()

    # Configure logger.
    logger.initLogger(None, args.verbosityLevel.upper())

    # Start linknx.
    linknx = Linknx(args.host, int(args.port))
    try:
        if requestType == 'read':
            objects = linknx.getObjects(objectIds=args.objectIds) if not args.regex else linknx.getObjects(patterns=args.objectIds)

            # No object.
            if not objects:
                logger.reportWarning('No such object.')
                sys.exit(10)

            # Count tabs to align columns.
            report = objects.getValues()
            longestId = max([len(obj) for obj in report.keys()])
            succeeds = True
            for o in sorted(report):
                v = report[o]
                spaceCount = longestId - len(o)
                spaces=''
                while spaceCount > 0:
                    spaces+=' '
                    spaceCount -= 1
                if args.value_only:
                    print('{0}'.format(v))
                else:
                    print('{0} {2} {1}'.format(o, v, spaces))

                if args.expected_value != None:
                    obj = linknx.getObject(o)
                    convertedExpectedValue = obj.convertValueToString(args.expected_value)
                    convertedObjectValue = obj.convertValueToString(v)
                    succeeds = succeeds and convertedExpectedValue == convertedObjectValue

            if not succeeds: exit(100)

        elif requestType == 'write':
            linknx.getObject(args.object).value = args.value
        elif requestType == 'execute':
            if args.action == None:
                action = ''.join(sys.stdin.readlines())
            else:
                action = args.action
            linknx.executeAction(action)
        else:
            raise Exception('Unsupported request type.')

    except Exception as e:
        logger.reportException()
        sys.exit(3)
