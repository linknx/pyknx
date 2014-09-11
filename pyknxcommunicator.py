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
Starts an instance of the Pyknx communicator daemon.
The daemon is aimed at listening for linknx events for object changes in order to call Python functions that are implemented in a script
that is passed to the daemon. This process allows for execution of Python code in reaction of object changes on linknx's end.
"""

import sys
import argparse
import signal
import time
import logging
from pyknx import logger
from pyknx.linknx import *
from pyknx.communicator import *

def parseAddress(addrStr, option):
    ix = addrStr.find(':')
    if ix < 0:
        raise Exception('Malformed value for ' + option +'. Expecting a tuple (hostname:port)')
    return (addrStr[0:ix], int(addrStr[ix + 1:]))

def makeArgumentParser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--comm-addr', dest='communicatorAddress', help='Address of the communicator. This argument must specify the hostname or the ip address followed by a colon and the port to listen on. Default is "localhost:1029"', default='localhost:1029')
    parser.add_argument('-l', '--linknx-addr', dest='linknxAddress', help='Address of the linknx server to bind to. This argument must specify the hostname or the ip address followed by a colon and the port. Default is "localhost:1028"', default='localhost:1028')
    parser.add_argument('userFile', help='use FILE as the user python script that implements callbacks functions declared in the linknx configuration (see the pyknxcallback attributes in XML).', metavar='FILE')
    parser.add_argument('--log-file', dest='logFile', help='write communicator\'s output to FILE rather than to standard output.', metavar='FILE', default=None)
    parser.add_argument('-d', '--daemonize', help='ask daemon to detach and run as a background daemon.', action='store_true', default=False)
    parser.add_argument('--pid-file', dest='pidFile', help='writes the PID of the daemon process to PIDFILE.', metavar='PIDFILE')
    parser.add_argument('-v', '--verbose', dest='verbosityLevel', help='set verbosity level. Default is "error".', metavar='LEVEL', choices=[l.lower() for l in logger.getLevelsToString()], default='error')
    return parser

if __name__ == '__main__':
    parser = makeArgumentParser(__doc__)
    args = parser.parse_args()

    # Configure logger.
    logger.initLogger(None, args.verbosityLevel.upper())

    args.communicatorAddress = parseAddress(args.communicatorAddress, 'communicator address')

    try:
        Communicator.run(args.linknxAddress, args.userFile, args.communicatorAddress, logFile=args.logFile, daemonizes=args.daemonize, pidFile=args.pidFile)
    except SystemExit:
        # This is a normal exit.
        pass
    except:
        logger.reportException()
