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
Let the communicator call a given function of the user script.

USAGE:
pyknxcall.py [-c communicatoraddress] [-a|--argument argname=argvalue [-a|--argument argname=argvalue [...]]] [-v level] functionName

OPTIONS:
    -c --comm-addr              Address of the communicator. This must be of the form <hostname:port> of <ipaddress:port>. Default is localhost:1029
    -a --argument               Argument to pass to user function. It is of the form argument_name=argument_value. Be careful not to insert whitespaces around the "=" sign.
    -v --verbose                Level of verbosity. Value must be one of the logging module (error, warning, info, debug)
    --help                      Display this help message and exit.

EXAMPLE:
    pyknxcall.py -a eventId=3 onEventStarted

    => calls the function onEventStarted in the user file with the -f argument of pyknxcommunicator.py. The implementation may look like this:
    def onEventStarted(context):
        print 'Event #{0} started.'.format(context.eventId)
"""

import sys
import getopt
import logging
from pyknx import logger, tcpsocket

def printUsage():
    print(__doc__)

def parseAddress(addrStr, option):
    ix = addrStr.find(':')
    if ix < 0:
        raise Exception('Malformed value for ' + option +'. Expecting a tuple (hostname:port)')
    return (addrStr[0:ix], int(addrStr[ix + 1:]))

if __name__ == '__main__':
    logger.initLogger(None, logging.INFO, usesDetailedLogging=False)
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'c:a:v:', ['comm-addr=', 'argument=', 'verbose=', 'help'])
    except getopt.GetoptError as err:
        logger.reportException()
        sys.exit(2)

    # Parse command line arguments.
    communicatorAddress = ('127.0.0.1',1029)
    arguments = []
    verbosity = logging.INFO
    for option, value in options:
        if option == '-c' or option == '--comm-addr':
            communicatorAddress = parseAddress(value, option)
        elif option == '-a' or option == '--argument':
            arguments.append(value)
        elif option == '--help':
            printUsage()
            sys.exit(1)
        elif option == '-v' or option == '--verbose':
            verbosity = logger.parseLevel(value)
        else:
            logger.reportError('Unrecognized option ' + option)
            sys.exit(2)

    if not remainder:
        logger.reportError('Missing function name.')
        printUsage()
        sys.exit(3)

    if len(remainder) > 1:
        logger.reportError('Too many arguments: {0}'.format(remainder))
        printUsage()
        sys.exit(4)

    functionName = remainder[0]

    # Init logger.
    logger.initLogger(None, verbosity, usesDetailedLogging=False)

    s = tcpsocket.Socket()
    s.connect(communicatorAddress)
    message=functionName
    for arg in arguments:
        message += '|{0}'.format(arg)
    s.sendString(message, endChar='$')

