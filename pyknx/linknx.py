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
import re
import getopt
import time
import collections
from xml.dom.minidom import parseString, Document, Element
from threading import *
from pyknx import tcpsocket, logger

class Linknx:
    class SendMessageThread(Thread):
        def __init__(self, name, message, commandName, linknx):
            Thread.__init__(self, name='SendMessageThread {1} (id={0})'.format(id(self), name))
            self.socket = tcpsocket.Socket()
            self.linknx = linknx
            self.messageWithEncodingHeader = '<?xml version="1.0" encoding="utf-8"?>' + message
            self.commandName = commandName
            self.finalStatus = None
            self.answerDom = None
            self.error = None

        def run(self):
            try:
                self.socket.connect((self.linknx.host, self.linknx.port))
                logger.reportDebug('Message sent to linknx: ' + self.messageWithEncodingHeader)
                answer = self.socket.sendString(self.messageWithEncodingHeader, encoding='utf8')
                while True:
                    logger.reportDebug('Linknx answered ' + answer)
                    answerDom = parseString(answer[0:answer.rfind(chr(4))])
                    execNodes = answerDom.getElementsByTagName(self.commandName)
                    status = execNodes[0].getAttribute("status")
                    if status == "ongoing":
                        # Wait for the final status.
                        answer = self.socket.waitForStringAnswer()
                        logger.reportDebug('New answer is {0}'.format(answer))
                    else:
                        if status != "success":
                            self.error = self._getErrorFromXML(execNodes[0])
                            logger.reportError(self.error)
                        self.finalStatus = status
                        self.answerDom = answerDom
                        break
            finally:
                self.socket.close()
                if self.is_alive(): logger.reportDebug('Thread is now stopped.')

        @property
        def isFinalized(self):
            return self.finalStatus != None

        def _getErrorFromXML(self, answer):
            errorMessage = ""
            for child in answer.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    errorMessage += child.data
            return errorMessage

    """
    The wrapper of an instance of Linknx.

    This class eases access to Linknx functionalities: it can retrieve objects (see getObject() and getObjects()), or configuration.
    """

    class InvalidObjectIdException(Exception):
        """ The object id is not valid in the Linknx instance. """
        def __init__(self, objectId):
            self._objectId = objectId

        def __str__(self):
            return 'Object {0} does not exist.'.format(self._objectId)

        def __repr__(self):
            return 'InvalidObjectIdException({0})'.format(self._objectId)

    def __init__(self, hostname='localhost', port=1028):
        """ Initialize a Linknx wrapper. """
        self._host = hostname
        self._port = port
        self._config = None
        self._objectConfig = None
        self._objects = {}

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def address(self):
        return (self._host, self._port)

    @property
    def emailServerInfo(self):
        emailServerElements = self.config.getElementsByTagName('emailserver')
        if len(emailServerElements) == 0:
            return None
        else:
            serverElt = emailServerElements[0]
            if serverElt.getAttribute('type') != 'smtp': return None
            host = serverElt.getAttribute('host').split(':')
            if len(host) != 2: return None
            fromAddr = serverElt.getAttribute('from')
            return (host[0], int(host[1]), fromAddr)

    @property
    def config(self):
        """
        Get the raw XML configuration currently used by the running Linknx instance.

        See objectConfig property for an alternative of these raw data.

        """

        if self._config is None:
            xmlConfig = self._sendMessage('Read Config', "<read><config></config></read>", 'read').getElementsByTagName('read')[0]
            self._config = xmlConfig.getElementsByTagName('config')[0]

        return self._config

    @property
    def objectConfig(self):
        """ Return a dictionary of the configuration of each Linknx object. Keys are object ids, values are ObjectConfig instances. """
        if not self._objectConfig:
            objectsConfigNode = self.config.getElementsByTagName('objects')[0]
            self._objectConfig = {} # key is objectId, value is an ObjectConfig
            for objectConfigNode in objectsConfigNode.getElementsByTagName('object'):
                objectConfig = ObjectConfig(objectConfigNode)
                self._objectConfig[objectConfig.id] = ObjectConfig(objectConfigNode)

        return self._objectConfig

    def executeAction(self, actionDetails):
        if isinstance(actionDetails, str):
            actionXML = actionDetails
        elif isinstance(actionDetails, Document):
            actionXML = actionDetails.childNodes[0].toxml()
        elif isinstance(actionDetails, Element):
            actionXML = actionDetails.toxml()
        else:
            raise Exception('Unsupported action details: must be a minidom XML document or element or an XML string.')

        # Build XML document to send to linknx.
        self._sendMessage('Execute {0}'.format(actionXML), '<execute>{action}</execute>'.format(action=actionXML), 'execute', waitsForAnswer=False)
        logger.reportDebug('Action execution has been sent to linknx.')

    def waitForRemoteConnectionReady(self):
        """
        Wait for Linknx's XML server to accept incoming connections.

        This method should be called if unsure about when the Linknx has been started. It may take some time to get ready.
        This method attempts to connect to Linknx during 10 seconds and raises an Exception if Linknx still is unreachable after this delay.

        """
        # Ask for config.
        logger.reportInfo('Start connecting to linknx on {0}.'.format(self.address))
        attemptId = 0
        maxAttemptCount = 10
        while attemptId < maxAttemptCount:
            attemptId += 1
            try:
                conf = self.config

                # Linknx is ready if we reach this point.
                logger.reportInfo('Linknx is up and ready, let\'s start.')
                return
            except ConnectionRefusedError:
                logger.reportInfo('Linknx is not yet ready...  (attempt {0}/{1})'.format(attemptId, maxAttemptCount))

            except Exception as e:
                logger.reportException()

            time.sleep(1)

        raise Exception('Linknx is not reachable.')

    def tryGetObject(self, id):
        try:
            return self.getObject(id)
        except Linknx.InvalidObjectIdException:
            return None

    def getObject(self, id):
        """ Get the object of given identifier. """
        if id is None: return None

        obj = self._objects.get(id)
        if obj is None:
            obj = Object(id, self)
            self._objects[id] = obj
        return obj

    def getObjects(self, patterns=None, objectIds=None):
        """ Get the objects whose identifiers are in the given list or match the given regex pattern. If neither a pattern nor object identifiers are provided, returns all objects. """
        actualPatterns = patterns if (not isinstance(patterns, str) or patterns == None) else (patterns,)

        objects = ObjectCollection(self)

        # Get object by ids.
        ids = set()
        if objectIds != None:
            for id in objectIds:
                objects.append(self.getObject(id))
                ids.add(id)

        # Handle regex.
        if actualPatterns != None:
            for pattern in actualPatterns:
                regex = re.compile(pattern)
                for id in self.objectConfig.keys():
                    if id in ids: continue
                    if regex.search(id) is None: continue
                    objects.append(self.getObject(id))
                    ids.add(id)

        # Get all objects if no constraint.
        if actualPatterns == None and objectIds == None:
            objects.extend([self.getObject(id) for id in self.objectConfig.keys()])
        return objects

    def _sendMessage(self, purpose, message, commandName, waitsForAnswer=True):
        """
        Sends an XML message to Linknx.

        This function is implemented mainly for internal purposes. The end user is unlikely to call it directly.
        message -- An XML request that follows Linknx XML protocol.
        commandName -- The name of the XML command that is sent.
        waitsForAnswer -- If True, this method blocks until linknx has sent its final status. Otherwise, the method returns immediately. Linknx's answer would then be logged when it arrives.
        Returns an XML document that corresponds to Linknx answer if waitsForAnswer is False, None otherwise.

        """
        # logger.reportDebug('Sending message to linknx: ' + message)
        messagingThread = Linknx.SendMessageThread(purpose, message, commandName, self)

        if waitsForAnswer:
            # CAUTION - PERFORMANCE WARNING
            # Call run() directly to avoid starting Thread. That will let the
            # current thread naturally block until run() returns with linknx's answer.
            # Otherwise, we would have to wait for SendMessageThread completion
            # in an infinite while loop with a harcoded sleep time at the end of
            # each iteration. A sleep time of 0.1s is too long in most cases (it
            # significantly slows down the overall request time) and a sleep
            # time of, say, 0.01 may still be too long in some cases. Client
            # expects our method to return as soon as possible.
            # Thread's work implementation may have been extracted into another
            # object to make things cleaner but reusing the Thread object is
            # quite straightforward.
            messagingThread.run()

            if messagingThread.finalStatus != 'success':
                raise Exception(messagingThread.error)

            return messagingThread.answerDom
        else:
            # Start thread and leave.
            # Do not care about final status here. Error would be logged by
            # messaging thread. Client does not want to wait for answer so not
            # notifying the error with an exception makes sense.
            messagingThread.start()
            return None

class ObjectConfig:
    def __init__(self, configNode):
        """    Configuration of an object in Linknx. """

        self.id = configNode.getAttribute('id')
        self.xml = configNode
        self.type = configNode.getAttribute('type')
        self.gad = configNode.getAttribute('gad')
        # self.callback = configNode.getAttribute('pyknxcallback')
        self.init = configNode.getAttribute('init') if configNode.hasAttribute('init') else 'request'
        self.flags = configNode.getAttribute('flags') if configNode.hasAttribute('flags') else 'cwtu'
        self.caption = ObjectConfig.getTextInElement(configNode, mustFind=False).strip('\n\t ')
        firstTypeDigit = self.type[0:self.type.find('.')]
        if firstTypeDigit == '1':
            self.typeCategory = 'bool'
        elif firstTypeDigit in ['5', '6', '7', '8', '9', '12', '13', '29']:
            if self.type in ('5.001', '5.003') or firstTypeDigit == '9':
                self.typeCategory='float'
            else:
                self.typeCategory = 'int'
        elif firstTypeDigit == '14':
            self.typeCategory = 'float'
        elif firstTypeDigit in ('4', '16', '28'):
            self.typeCategory = 'string'
        elif firstTypeDigit == '10':
            self.typeCategory = 'time'
        elif firstTypeDigit == '11':
            self.typeCategory = 'date'
        else:
            logger.reportWarning('Object ' + self.id + ' has an unsupported type ' + self.type)
            self.typeCategory = 'unknown'

    @staticmethod
    def getTextInElement(elt, mustFind = True):
        text = ''
        for node in elt.childNodes:
            if node.nodeType == node.TEXT_NODE:
                # if text:
                    # raise Exception('Multiple text nodes in the same element are not supported.')
                text = text + node.data

        if mustFind and not text:
            raise Exception('Missing text in element {0}'.format(elt.nodeName))
        return text

class Object(object):

    """ Linknx object. """

    def __init__(self, id, linknx):
        """
        Initialize an object from Linknx.

        id -- Identifier of the object. Corresponds to the id attribute in XML configuration.
        linknx -- Linknx instance that provides the object.
        """
        self._id = id
        self._linknx = linknx
        if not id in linknx.objectConfig:
            raise Linknx.InvalidObjectIdException(id)

        self._objectConfig = linknx.objectConfig[id]

    @property
    def id(self):
        """ Object identifier. This is the id attribute in XML configuration. """
        return self._id

    @property
    def caption(self):
        """ Object caption. This is the text of the object element in the XML configuration. """
        return self._objectConfig.caption

    @property
    def gad(self):
        """ Group Address of the object. This is the gad attribute in XML configuration. """
        return self._objectConfig.gad

    @property
    def linknx(self):
        """ Return the Linknx instance that provides the object. """
        return self._linknx

    @property
    def xml(self):
        """ Return the xml element corresponding to this object in Linknx configuration. """
        return self._objectConfig.xml

    @property
    def type(self):
        """ Return the string corresponding to the type attribute in XML configuration. """
        self._objectConfig.type

    @property
    def value(self):
        """ Read object's value from linknx. """
        objects = ObjectCollection(self.linknx, (self,))
        return objects.getValues()[self.id]

    def convertValueToString(self, objValue):
        if self._objectConfig.typeCategory == 'bool':
            if isinstance(objValue, bool):
                objectValue = 'on' if objValue else 'off'
            else:
                objValueStr = str(objValue).lower()
                if objValueStr in ['true', 'on', 'yes', '1']:
                    objectValue = 'on'
                elif objValueStr in ['false', 'off', 'no', '0']:
                    objectValue = 'off'
                else:
                    raise Exception('For object {1}: Unable to convert {0} to boolean.'.format(objValue, self._id))
        elif self._objectConfig.typeCategory in ('int', 'float', 'string', 'date', 'time'):
            objectValue = str(objValue)
        else:
            raise Exception('Unsupported type ' + self._objectConfig.typeCategory)

        return objectValue

    def convertStringToValue(self, valueString):
        if self._objectConfig.typeCategory == 'bool':
            return valueString in ['on', '1', 'yes', 'true']
        elif self._objectConfig.typeCategory == 'int':
            return int(valueString)
        elif self._objectConfig.typeCategory == 'float':
            return float(valueString)
        else:
            return valueString

    @value.setter
    def value(self, objValue):
        """ Write object's value to linknx. """
        # Convert value to the linknx format.
        logger.reportDebug('Attempting to set value of {0} to {1}'.format(self._id, objValue))
        objectValue = self.convertValueToString(objValue)

        if not objValue is objectValue:
            logger.reportDebug('Value has been converted to ' + str(objectValue))

        # Initialize DOM with a simple string, then use minidom to write
        # attributes so that special characters are properly encoded (for
        # instance, &ampersand; in place of &, etc).
        messageDom = parseString('<write><object/></write>')
        objectNode = messageDom.getElementsByTagName('object')[0]
        objectNode.setAttribute('id', self._id)
        objectNode.setAttribute('value', objectValue)
        answerDom = self._linknx._sendMessage('Write {0}={1}'.format(self.id, objValue), messageDom.toxml(), 'write')

    def __repr__(self):
        return self.id

    def __str__(self):
        return self.id

class ObjectCollection(list):
    def __init__(self, linknx, objects=[]):
        self._linknx = linknx
        self.extend([o if isinstance(o, Object) else linknx.getObject(o) for o in objects])

    def getValues(self):
        """ Returns a dictionary with object identifiers as keys and object values as values. """
        objectRequests = ['<object id="{id}"/>'.format(id=object.id) for object in self]
        message = '<read><objects>{objects}</objects></read>'.format(objects=''.join(objectRequests))

        answerDom = self._linknx._sendMessage('Read {0}'.format(self), message, 'read')

        # Extract all object values from linknx's answer and store them by
        # object id.
        readNodes = answerDom.getElementsByTagName("read")
        valueStr = None
        objectValueStringsById = {}
        objectsNodes = readNodes[0].getElementsByTagName("objects")
        objectNodes = objectsNodes[0].getElementsByTagName("object")
        for objectNode in objectNodes:
            objectId = objectNode.getAttribute("id")
            objectValueStringsById[objectId] = objectNode.getAttribute("value")

        # Make sure we have a value for each requested object.
        objectValues = {}
        for obj in self:
            if not obj.id in objectValueStringsById:
                raise Exception("Failed to evaluate object {0}.".format(obj))
            objectValues[obj.id] = obj.convertStringToValue(objectValueStringsById[obj.id]) 

        return objectValues
