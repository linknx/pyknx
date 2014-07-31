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
Logging module for pyknx.

This module is based on the standard logging module and adapted to better suit pyknx needs.
This module automatically adds a handler for signal USR1, which should be sent to notify the application that its log file has been moved and must be reloaded.
"""

import logging
import traceback
import os.path
import sys
import signal

logHandlers = []
stdOutLog = None # None to disable stdout logging, otherwise log level.
fileLog = None # Tuple (filename, level)

def getLevelsToString():
    return ('ERROR', 'WARNING', 'INFO', 'DEBUG')

def initLogger(fileLogInfo=None, stdoutLogLevel=logging.INFO, usesDetailedLogging=True):
    """
    Initialize the logging system. Should be called prior to any other function of this module.

    fileLogInfo -- A tuple that contains the log filename and log verbosity. Should be None to deactivate file logging.
    stdoutLogLevel -- Verbosity level to use when writing log to stdout. Should be None to deactivate logging to stdout.

    """
    global logHandler
    global logFilename
    global logLevel

    _setHandlers(None, None)
    _setHandlers(fileLogInfo, stdoutLogLevel, usesDetailedLogging)
    logging.getLogger().setLevel(logging.DEBUG)
    signal.signal(signal.SIGUSR1, _usr1SignalHandler)
    reportDebug('Logger initialized with fileLogInfo={fli} stdoutLogLevel={stdoutLL} usesDetailedLogging={usesDetailedLogging}.'.format(fli=fileLogInfo, stdoutLL=stdoutLogLevel, usesDetailedLogging=usesDetailedLogging))

def parseLevel(levelToString):
    """    Parses a string that represents the log level. The string should be the same than the level in the logging module. """
    lValue = levelToString.lower()
    if lValue == 'error':
        return logging.ERROR
    elif lValue == 'warning':
        return logging.WARNING
    elif lValue == 'info':
        return logging.INFO
    elif lValue == 'debug':
        return logging.DEBUG
    else:
        raise Exception('Unknown verbosity level ' + levelToString)

def _setHandlers(fileLogInfo, stdoutLogLevel, usesDetailedLogging=True):
    global logHandlers
    global fileLog
    global stdOutLogLevel

    logger = logging.getLogger()

    # Remove previous handlers.
    for handler in logHandlers:
        logger.removeHandler(handler)
        if isinstance(handler, logging.FileHandler):
            handler.close()

    if not fileLogInfo is None and not isinstance(fileLogInfo, tuple):
        raise Exception('File log info should be specified with a tuple (filename, loglevel).')

    fileLog = fileLogInfo
    if(isinstance(fileLog, tuple) and isinstance(fileLog[1], str)):
            fileLog = (fileLog[0], parseLevel(fileLog[1]))
    stdOutLog = stdoutLogLevel
    if(isinstance(stdOutLog, str)):
        stdOutLog = parseLevel(stdOutLog)

    # Create new handlers.
    logHandlers = []
    if not fileLog is None:
        dir = os.path.normpath(os.path.dirname(fileLog[0]))
        if not os.path.isdir(dir):
            os.makedirs(dir)

        _addHandler(logging.FileHandler(fileLog[0]), fileLog[1], usesDetailedLogging)
    if not stdOutLog is None:
        _addHandler(logging.StreamHandler(), stdOutLog, usesDetailedLogging)

def _addHandler(handler, logLevel, usesDetailedLogging=True):
    global logHandlers

    handler.setLevel(logLevel)
    logHandlers.append(handler)
    if usesDetailedLogging:
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(threadName)s] [%(callerfilename)s:%(callerlineno)d] %(message)s')
    else:
        formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def _usr1SignalHandler(signalNumber, frame):
    if signalNumber == signal.SIGUSR1:
        reportInfo('USR1 signal caught. Means that log file has to be reloaded.')
        _setHandlers(fileLog, stdOutLog)

def _reportMessage(message, level):
    stack = traceback.extract_stack()
    frame = stack[len(stack) -3]
    extraDict={'callerfilename' : os.path.basename(frame[0]), 'callerlineno' : frame[1]}
    logging.getLogger().log(level, message, extra=extraDict)

def reportDebug(message):
    """ Reports a debug message. """
    _reportMessage(message, logging.DEBUG)

def reportError(message):
    """ Reports an error message. """
    _reportMessage(message, logging.ERROR)
    # logging.getLogger().error(message)

def reportWarning(message):
    """ Reports a warning message. """
    _reportMessage(message, logging.WARNING)
    # logging.getLogger().warning(message)

def reportInfo(message):
    """ Reports an informational message. """
    _reportMessage(message, logging.INFO)
    # logging.getLogger().info(message)

def reportException(message=None):
    """ Reports an exception. Exception info is gotten from sys.exc_info(). """
    if not message: message = 'Exception caught.'
    _reportMessage(message + ' Traceback is:\n' + traceback.format_exc(), logging.ERROR)
