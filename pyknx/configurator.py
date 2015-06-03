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

from xml.dom.minidom import parse, parseString
from pyknx.linknx import ObjectConfig
from pyknx import logger
import sys
import getopt
import codecs
import logging
import socket

class Configurator:
    """ Object able to automatically patch the linknx configuration xml to add python bindings. """
    def __init__(self, sourceFile, outputFile, address, communicatorName='pyknx'):
        self._address = address
        self._sourceFile = sourceFile
        self._outputFile = outputFile
        self._communicatorName = communicatorName
        self._config = None

    @property
    def config(self):
        if not self._config:
            if self._sourceFile != None:
                doc = parse(self._sourceFile)
            else:
                # Read from standard input.
                doc = parseString(self.readFileFromStdIn())
            self._config = doc.getElementsByTagName('config')[0]

        return self._config

    @property
    def callbackAttributeName(self):
        return '{0}callback'.format(self._communicatorName)

    def readFileFromStdIn(self):
        return ''.join(sys.stdin.readlines())

    def cleanConfig(self):
        # Delete all pyknx rules before creating only those that apply to the
        # current config.
        rulesNode = self._getOrAddConfigElement(self.config, 'rules')
        prefixLength = len(self._communicatorName)
        configuredAtLeastOne = False
        for ruleNode in rulesNode.getElementsByTagName('rule'):
            ruleId = ruleNode.getAttribute('id')
            if ruleId[:prefixLength] == self._communicatorName:
                configuredAtLeastOne = True
                logger.reportInfo('Clean rule ' + ruleId + ' coming from a previous configure.')
                rulesNode.removeChild(ruleNode)

        if not configuredAtLeastOne:
            logger.reportInfo('Input XML config does not define any pyknx rule. Nothing to clean.')

        servicesNode = self._getOrAddConfigElement(self.config, 'services')
        ioportsNode = self._getOrAddConfigElement(servicesNode, 'ioports')
        for ioportNode in ioportsNode.getElementsByTagName('ioport'):
            if ioportNode.getAttribute('id') == self._communicatorName:
                logger.reportInfo('Clean ' + ioportNode.toxml())
                ioportsNode.removeChild(ioportNode)

    def createActionNode(self, callbackName, args):
        doc = self.config.ownerDocument
        actionNode = doc.createElement('action')
        actionNode.setAttribute('type', 'ioport-tx')
        actionNode.setAttribute('ioport', self._communicatorName)
        dataStr = callbackName
        if not args is None:
            for argName, argValue in args.items():
                dataStr += '|{0}={1}'.format(argName, argValue)
        actionNode.setAttribute('data', dataStr + '$')
        return actionNode

    def generateConfig(self):
        # Read xml to get pyknx special attributes.
        config = self.config
        doc = config.ownerDocument
        rulesNode = self._getOrAddConfigElement(config, 'rules')

        # Generate a rule for each object that has a callback in the user file.
        objectNodes = config.getElementsByTagName('objects')[0]
        configuredAtLeastOne = False
        definesLegacyCallbackAttribute = False
        callbackAttributeName = self.callbackAttributeName
        for objectNode in objectNodes.getElementsByTagName('object'):
            objectConfig = ObjectConfig(objectNode)
            objectId = objectConfig.id
            callback = objectNode.getAttribute(callbackAttributeName)
            if callback == None or callback == '':
                if objectNode.getAttribute('pyknxcallback'):
                    logger.reportError('pyknxcallback found on {0}'.format(objectNode.toxml()))
                    definesLegacyCallbackAttribute = True
                logger.reportDebug('No callback found for object ' + objectConfig.id + ' (no {0} attribute for this object)'.format(callbackAttributeName))
                continue

            configuredAtLeastOne = True
            ruleNode = doc.createElement('rule')
            ruleId = '{0}{1}'.format(self._communicatorName, objectId)
            logger.reportInfo('Generating rule {0}'.format(ruleId))
            ruleNode.setAttribute('id', ruleId)
            ruleNode.setAttribute('init', 'false')
            conditionNode = doc.createElement('condition')
            conditionNode.setAttribute('type', 'object')
            conditionNode.setAttribute('id', objectId)
            # conditionNode.setAttribute('value', objectConfig.defaultValue)
            conditionNode.setAttribute('trigger', 'true')
            ruleNode.appendChild(conditionNode)
            actionListNode = doc.createElement('actionlist')
            actionListNode.setAttribute('type', 'if-true')
            ruleNode.appendChild(actionListNode)
            actionNode = self.createActionNode(callback, {'objectId' : objectId})
            actionListNode.appendChild(actionNode)
            # actionListIfFalseNode = actionListNode.cloneNode(True)
            # actionListIfFalseNode.setAttribute('type', 'on-false')
            # # ruleNode.appendChild(actionListIfFalseNode)
            rulesNode.appendChild(ruleNode)

        if not configuredAtLeastOne:
            logger.reportInfo('Nothing to do. None of the objects does define a callback attribute.')
            if definesLegacyCallbackAttribute:
                logger.reportWarning('There is at least one pyknxcallback attribute in the config file. These attributes were recognized by Pyknx before version 2.2. Did you forget to rename them to {0}?'.format(callbackAttributeName))
        else:
            # Add an ioport service for the communicator.
            servicesNode = self._getOrAddConfigElement(config, 'services')
            ioportsNode = self._getOrAddConfigElement(servicesNode, 'ioports')
            ioportNode = doc.createElement('ioport')
            ioportNode.setAttribute('id', self._communicatorName)
            try:
                hostIP = socket.gethostbyname(self._address[0])
            except:
                logger.reportWarning('Could not check that {0} is a valid ip address. Please check the output configuration. Linknx does not support hostnames, it requires IP address.'.format(self._address[0]))
                hostIP = self._address[0]
            ioportNode.setAttribute('host', hostIP) #gethostbyname converts the hostname into an ip. Linknx does not support ioport hostnames.
            ioportNode.setAttribute('port', str(self._address[1]))
            ioportNode.setAttribute('type', 'tcp')
            ioportsNode.appendChild(ioportNode)


    def writeConfig(self):
        if self._outputFile != None:
            outputXMLFile = codecs.open(self._outputFile, mode='w', encoding='utf-8')
            outputXMLFile.write(self.config.toxml())
            outputXMLFile.close()
            logger.reportInfo('Output config written to ' + self._outputFile)
        else:
            print(self.config.toxml())


    def _getOrAddConfigElement(self, parent, elementTagName):
        elementNodes = parent.getElementsByTagName(elementTagName)
        if not elementNodes:
            elementNode = parent.ownerDocument.createElement(elementTagName)
            parent.appendChild(elementNode)
            logger.reportInfo('No <' + elementTagName + '> element in config, creating one.')
        else:
            elementNode = elementNodes[0]
        return elementNode
