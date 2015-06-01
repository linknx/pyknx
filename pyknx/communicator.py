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

import sys
import getopt
import time
import os.path
import logging
import importlib
import signal
from threading import *
from pyknx import tcpsocket, logger
from pyknx.linknx import *

class CallbackContext(object):

    """
    The context of the call of one of the user-defined functions, either from Linknx or from pyknxcall.py.

    This class always exposes the communicator and Linknx instances.
    When call is issued as a consequence of an object value change in Linknx, the context also provides the object that changed.
    When call is issued from pyknxcall.py script all extra arguments provided on the command line are accessible through homonym properties. For instance, when executing 'pyknxcall.py -amyArg=foo myFunction'
    the function myFunction is passed an instance of CallbackContext which contains a member named 'myArg' and whose value is 'foo'.

    """

    def __init__(self, communicator, args={}):
        # if not args is None and args.has_key('objectId'):
            # self._object = linknx.getObject(args['objectId'])
        # else:
            # self._object = None
        self._communicator = communicator
        self._args = args

        # Create members for easy access.
        if args != None:
            exp = re.compile('[^0-9a-zA-Z_]')
            for argName, argValue in args.items():
                # Rename args to comply with Python naming rules.
                changedName = re.sub(exp, '_', argName)
                if changedName != argName:
                    logger.reportWarning('Argument {0} renamed to {1} to comply with naming rules.'.format(argName, changedName))

                # Create argument.
                vars(self)[changedName] = argValue

        if 'objectId' in vars(self):
            self._object = self.linknx.getObject(self.objectId)
        else:
            self._object = None

    @property
    def object(self):
        """ A wrapper of the Linknx object that is related to the event. """
        return self._object

    @property
    def linknx(self):
        """ The instance of the Linknx wrapper the communicator is linked with. """
        return self._communicator.linknx

    @property
    def communicator(self):
        """ The instance of the pyknx communicator that receives events either from Linknx or from the pyknxcall.py utility script. """
        return self._communicator

    @property
    def customArgs(self):
        """
        A dictionary that contains all arguments of the user-defined function call.

        Keys are the argument names, values their corresponding argument value.
        """
        return self._args

    def getArgument(self, argName, defaultValue = None):
        """
        A convenience method that allows to get the value of a given argument.

        This method is equivalent to searching in the customArgs dictionary.
        argName -- The name of the argument to get.
        defaultValue -- The value to return if no such argument is found in this context.

        """

        if argName in self.customArgs:
            return self.customArgs[argName]
        else:
            return defaultValue

    def __str__(self):
        return str(self._args)

class Communicator:

    """
    The communicator daemon that is intended to be executed once Linknx is started.

    This daemon continuously listens on its dedicated port for incoming data either from Linknx or from the pyknxcall.py utility script.
    It is aimed at performing calls of functions in the user-defined file specified in the initializer of the class.

    """
    class Listener(Thread):
        """ Thread that listens for incoming connection from linknx. """
        def __init__(self, address, communicator):
            Thread.__init__(self, name='Communicator Listening Thread')
            self._address = address
            self._isStopRequested = False
            self._socket = tcpsocket.Socket() # socket to listen on for information coming from linknx.
            self._communicator = communicator
            self.linknx = self._communicator.linknx
            self.isReady = False

        def isListening(self):
            return not self._socket is None and self.isReady
        @property
        def isStopped(self):
            return self._socket is None

        def run(self):
            logger.reportInfo('Listening on ' + str(self._address))
            self._isStopRequested = False
            try:
                self._socket.bind(self._address)

                # Thread loop.
                while not self._isStopRequested:
                    self.isReady = True
                    data, conn = self._socket.waitForString(endChar='$')
                    # Throw data away if script has not been initialized yet.
                    # See startListening for details.
                    if data is None or not self._communicator.isUserScriptInitialized:
                        time.sleep(0.1)
                        continue

                    logger.reportDebug('Data received: {0}'.format(data))

                    # Handle request.
                    tokens = data.split('|')
                    callbackName = tokens[0]
                    # Parse arguments. First is object id.
                    args={}
                    for token in tokens[1:]:
                        argName, sep, argValue = token.partition('=')
                        if argValue: argValue = argValue.strip()
                        args[argName.strip()] = argValue
                    context = CallbackContext(self, args)
                    res = self._communicator._executeUserCallback(callbackName, context)
                    if res:
                        conn.sendall(res + '$')
                    conn.close()
            except Exception as e:
                logger.reportException()
            finally:
                logger.reportDebug('Closing socket...')
                self._socket.close()
                logger.reportInfo('Socket closed. Listening terminated.')
                self._socket = None

        def stop(self):
            logger.reportInfo('Stopping listener thread...')
            self._isStopRequested = True

    def __init__(self, linknx, userFile, address=('localhost',1029), userScriptArgs={}):

        """
        Initialize the daemon.

        linknx -- The wrapper of the Linknx server to communicate with.
        userFile -- The file that implements the user-defined functions to be called when objects which have a callback attribute in the Linknx configuration change.
        address -- The address the communicator will listen on, defined as a tuple (ip address, port). The default is ('localhost', 1029).
        userScriptArgs -- A dictionary of extra arguments to expose in the CallbackContext instance passed to the initializeUserScript function (if implemented in the user file). It defaults to empty.

        """
        self._address = address
        self._listenerThread = None # thread that owns the listening socket, None if not listening.
        self._userFile = userFile
        self._linknx = linknx
        self._userModule = None
        self._userScriptArgs = userScriptArgs
        self.isUserScriptInitialized = False

    @property
    def isListening(self):
        """ Tell whether the communicator is currently listening for incoming data. """
        return not self._listenerThread is None

    @property
    def linknx(self):
        """ Return the wrapper of the Linknx instance the communicator is working with. """
        return self._linknx

    @property
    def address(self):
        """ Return the listening address as a tuple (ip address, port). """
        return self._address

    def _loadUserFile(self):
        # Append the directory that contains the user script to python path.
        if self._userFile:
            dirName, fileName = os.path.split(self._userFile)
            dirName = os.path.abspath(dirName)
            moduleName, fileExt = os.path.splitext(fileName)
            sys.path.append(dirName)
            logger.reportDebug('_loadUserFile: moduleName={0} fileExt={1} dirName={2}'.format(moduleName, fileExt, dirName))
            self._userModule = importlib.import_module(moduleName)
            logger.reportDebug('Imported {0}'.format(self._userModule.__file__))
            return True
        else:
            logger.reportError('No user file specified.')
            return False

    @staticmethod
    def run(linknxAddress, userFile, communicatorAddress, userScriptArgs=None, verbosityLevel=logging.INFO, logFile=None, daemonizes=False, pidFile=None):
        def signal_handler(signal, frame):
            logger.reportInfo('Terminating...')
            communicator.stopListening()

        # Init logger.
        if not logFile is None:
            logger.initLogger((logFile, verbosityLevel), None)
        else:
            logger.initLogger(None, verbosityLevel)

        if isinstance(linknxAddress, tuple):
            linknxAddr = (linknxAddress[0], int(linknxAddress[1]))
        elif isinstance(linknxAddress, str):
            tokens = linknxAddress.split(':')
            linknxAddr = (tokens[0], int(tokens[1]))
        else:
                raise Exception('Unrecognized linknx address format.')
        linknx = Linknx(linknxAddr[0], int(linknxAddr[1]))

        # Fork if requested.
        if daemonizes:
            pid = os.fork()
        else:
            pid = os.getpid()

        if pid != 0 and pidFile != None:
            with open(pidFile, 'w') as f:
                f.write(str(pid))

        # If we are in the parent process (when forking), there is nothing left
        # to do. The communicator should run in the child process.
        if pid != 0 and daemonizes:
            return

        # Start communicator.
        communicator = Communicator(linknx, userFile, communicatorAddress, userScriptArgs=userScriptArgs)
        communicator.startListening()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Main loop.
        while communicator.isListening:
            time.sleep(1)

        # Clean pid file.
        if pidFile != None and os.path.exists(pidFile):
            os.remove(pidFile)

    def startListening(self):

        """
        Start the communicator. It is then waiting for incoming information from Linknx.

        If provided, the initializeUserScript function of the user file is called. Its context contains the arguments that were optionally given to the __init__ method.

        """
        if self.isListening: return

        # Make sure linknx is ready.
        self.linknx.waitForRemoteConnectionReady()

        # Start listening early to avoid communication errors from linknx. Those
        # errors are never harmful but the user may be surprized and worried
        # about them! 
        self._listenerThread = Communicator.Listener(self._address, self)
        self._listenerThread.start()
        timeout = time.time() + 4
        while not self._listenerThread.isReady and time.time() < timeout:
            time.sleep(0.3)
        if not self._listenerThread.isReady:
            raise Exception('Could not initialize listening socket.')

        # Initialize user-provided script. The purpose of this callback is to
        # let the user initialize its script by reading state from linknx (and
        # possibly anywhere else). Thus, linknx should not raise events yet,
        # since user script would likely be partially initialized. The
        # isUserScriptInitialized flag is used for that purpose.
        if self._loadUserFile():
            logger.reportInfo('Initializing user script...')
            try:
                self._executeUserCallback('initializeUserScript', CallbackContext(self, args=self._userScriptArgs), True)
            except Exception as e:
                logger.reportException('User script initialization failed, communicator will stop immediately.')
                self.stopListening()
                return
            logger.reportInfo('User script initialized.')
        self.isUserScriptInitialized = True


    def stopListening(self):
        """ Stop communicator. No new incoming connection will be possible. """
        # Notify user script first. This allows linknx to notify a few object
        # changes before communicator really stop listening.
        if self._userFile and self.isUserScriptInitialized:
            self._executeUserCallback('finalizeUserScript', CallbackContext(self), True)
            logger.reportInfo('User script finalized.')

        if not self.isListening: return
        self._listenerThread.stop()

        # Wait for listener thread to end (to be sure that no callback
        # request originating from linknx can reach the user script anymore).
        while not self._listenerThread.isStopped:
            time.sleep(0.5)
        self._listenerThread = None

        if self._userFile:
            self._executeUserCallback('endUserScript', CallbackContext(self), True)
            logger.reportInfo('User script ended.')

    def _executeUserCallback(self, callbackName, context, isOptional=False):
        try:
            if hasattr(self._userModule, callbackName):
                logger.reportDebug('Calling user callback {0} with context {1}'.format(callbackName, context))
                callback = getattr(self._userModule, callbackName)
                res = callback(context)
                logger.reportDebug('Callback {0} returned {1}'.format(callbackName, res))
                return res
            else:
                message='No function {0} defined in {1}'.format(callbackName, self._userFile)
                if isOptional:
                    logger.reportInfo(message + ', skipping')
                else:
                    logger.reportWarning(message)
        except Exception as e:
            logger.reportException('User code execution failed.')
