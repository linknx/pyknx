#!/usr/bin/python3

# Copyright (C) 2012-2013 Cyrille Defranoux
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
Lightweight command line client for linknx. It is aimed at reading or writing object values from/to linknx.
When reading objects, this script outputs a line per object, each line composed of the object id and its corresponding value separated by spaces.

SYNTAX:
        pyknxclient.py [-h host] [-p port] [-v level] -r id1 [-r id2 [...]]
        pyknxclient.py [-h host] [-p port] [-v level] -R pattern
        pyknxclient.py [-h host] [-p port] [-v level] -w id value

        Where id, id1, id2, ... are object identifiers specified in the linknx configuration XML with the 'id' attribute.

OPTIONS:
        -h, --host      Hostname of the machine running the linknx daemon (default is 'localhost').
        -p, --port      Port linknx listens on (default is 1028).
        -v, --verbose   Level of verbosity. Value must be one of the logging module (error, warning, info, debug)
        -r, --read      Read value of object with given id. Can occur multiple times with various identifiers.
        -R, --regex     Read value of all objects whose identifiers match the given regex pattern. The pattern must comply with the 're' python module.
        -w, --write     Writes a new value to the object of given identifier.
            --help      Display this help message and quit.

EXAMPLES:
        Read all objects:
            pyknxclient.py -R ".*"

        Read two objects:
            pyknxclient.py -r KitchenLights -r LivingRoomLights

        Turn off kitchen lights:
            pyknxclient.py -w KitchenLights off
            pyknxclient.py -w KitchenLights false
            pyknxclient.py -w KitchenLights 0
"""

import sys
import getopt
import traceback
import logging
from xml.dom.minidom import parseString
from threading import *
from pyknx import logger
from pyknx.linknx import *

def printUsage():
    print(__doc__)

if __name__ == '__main__':
    logger.initLogger(None, logging.INFO, usesDetailedLogging=False)

    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'r:w:h:p:v:R:', ['read=', 'write=', 'regex=', 'host=', 'port=','verbose=','help'])
    except getopt.GetoptError as err:
        logger.reportError(sys.exc_info()[1])
        sys.exit(2)

    print('*******************')
    print('DEPRECATION NOTICE:')
    print('*******************')
    print('This script is now deprecated and its functionalities have been split into the two scripts pyknxread.py and pyknxwrite.py. An additional script named pyknxexecute.py allows for executing actions (which functionality is not handled by pyknxclient.py at all).')

    # Parse command line arguments.
    reads = False
    writes = False
    objectIds = []
    isRegex = False
    host = 'localhost'
    port = 1028
    verbosity = logging.WARNING
    for option, value in options:
        if option == '-r' or option == '--read':
            reads = True
            objectIds.append(value)
        elif option == '-R' or option == '--regex':
            reads = True
            objectIds.append(value)
            isRegex = True
        elif option == '-w' or option == '--write':
            writes = True
            objectIds.append(value)
        elif option == '-h' or option == '--host':
            host = value
        elif option == '-p' or option == '--port':
            port = value
        elif option == '-v' or option == '--verbose':
            verbosity = logger.parseLevel(value)
        elif option == '--help':
            printUsage()
            sys.exit(1)
        else:
            print('Unrecognized option ' + option)
            sys.exit(2)

    logger.initLogger(None, verbosity, usesDetailedLogging=False)

    if reads == writes:
        logger.reportError('Expecting -r|--read or -w|--write and not both.')
        sys.exit(2)

    if writes and len(objectIds) > 1:
        logger.reportError('Can only write one object.')
        sys.exit(2)

    valueToWrite = None
    if writes:
        if not remainder:
            print('No value specified.')
            printUsage()
            sys.exit(3)
        valueToWrite = remainder[0]
        del remainder[0]

    if remainder:
        logger.reportError('Too many arguments: ' + str(remainder))
        sys.exit(4)

    # Start linknx.
    linknx = Linknx(host, int(port))
    try:
        if reads:
            report={}
            if not isRegex:
                for objId in objectIds:
                    report[objId] = linknx.getObject(objId).value
            else:
                for obj in linknx.getObjects(objectIds[0]):
                    report[obj.id] = obj.value

            # No object.
            if not report:
                logger.reportWarning('No object of given id.')
                sys.exit(10)

            # Count tabs to align columns.
            longestId = max([len(id) for id in report.keys()])
            for o, v in report.items():
                spaceCount = longestId - len(o)
                spaces=''
                while spaceCount > 0:
                    spaces+=' '
                    spaceCount -= 1
                print('{0} {2} {1}'.format(o, v, spaces))
        elif writes:
            linknx.getObject(objectIds[0]).value = valueToWrite
    except Exception as e:
        if verbosity == logging.DEBUG:
            logger.reportException()
        else:
            logger.reportError(sys.exc_info()[1])
        sys.exit(3)
