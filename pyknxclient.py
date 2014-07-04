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
Lightweight command line client for linknx. It is aimed at reading or writing object values from/to linknx or to executing actions.
"""

import sys
import argparse
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

	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('-s', '--server', dest='host', help='Hostname of the machine running the linknx daemon. Default is localhost.', default='localhost')
	parser.add_argument('-p', '--port', dest='port', help='Port linknx listens on. Default is 1028.', default=1028)
	parser.add_argument('action', help='Action to perform. ACTION can be one of {read, write, execute}.', metavar='ACTION', choices=('read', 'write', 'execute'))
	parser.add_argument('argument', help='Action\'s argument, whose meaning depends on the action type. When ACTION=read or ACTION=write, ARG represents the identifier of the object to touch. If ACTION=execute, this is the XML representation of the action to execute (for instance <action type="set-value" id="kitchen_heating" value="comfort"/>.', metavar='ARG')
	parser.add_argument('-R', '--regex', action='store_true', help='When used in conjunction with ACTION=read, ARG is interpreted as a regex and used to find objects to read. The pattern must comply with the \'re\' python module.')
	parser.add_argument('--value-only', action='store_true', help='When used in conjunction with ACTION=read, outputs the value of the queried object but do not prefix it with the object\'s id.')
	parser.add_argument('--expected-value', help='When used in conjunction with ACTION=read, represents the expected value of the object. This script will exit with a non-zero return code if the value is not the expected one. This is useful when using this script in a "if" test of a shell script.')
	parser.add_argument('-v', '--verbose', dest='verbosityLevel', help='set verbosity level. Default is "error".', metavar='LEVEL', choices=[l.lower() for l in logger.getLevelsToString()], default='error')
	args = parser.parse_args()

	# Configure logger.
	logger.initLogger(None, args.verbosityLevel.upper())

	if args.action != 'read' and args.regex:
		raise Exception('Regular expression can be used with ACTION=read only.')

	# Start linknx.
	linknx = Linknx(args.host, int(args.port))
	try:
		if args.action == 'read':
			report = {}
			if not args.regex:
				report[args.argument] = linknx.getObject(args.argument).value
			else:
				for obj in linknx.getObjects(args.argument):
					report[obj.id] = obj.value

			# No object.
			if not report:
				logger.reportWarning('No object of given id.')
				sys.exit(10)

			# Count tabs to align columns.
			longestId = max([len(id) for id in report.keys()])
			succeeds = True
			for o, v in report.items():
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

		elif args.action == 'write':
			linknx.getObject(args.argument).value = valueToWrite
		elif args.action == 'execute':
			linknx.executeAction(args.argument)
		else:
			raise Exception('Unsupported action {0}'.format(args.action))

	except Exception as e:
		if args.verbosityLevel.lower() == "debug":
			logger.reportException()
		else:
			logger.reportError(sys.exc_info()[1])
		sys.exit(3)
