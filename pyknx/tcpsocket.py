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

import socket
from pyknx import logger

class Socket:
    def __init__(self):
        self._socket = socket.socket()
        self._socket.settimeout(5)
        # self._socket.setblocking(1)

    def bind(self, address):
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(address)
        self._socket.listen(5)

    def connect(self, address):
        self._socket.connect(address)

    def close(self):
        # self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def waitForString(self, encoding = 'utf8', endChar=chr(4)):
        responseBytes, connection = self.waitForData(endChar.encode(encoding))
        if connection is None:
            return (None, None)
        else:
            return (responseBytes.decode(encoding), connection)

    def waitForData(self, endChar = chr(4)):
        # Wait for a connection.
        try:
            conn, address = self._socket.accept()
        except socket.timeout:
            return (None, None)

        # Read incoming data.
        data = b''
        while True:
            try:
                chunk = conn.recv(4)
                endCharIx = chunk.find(endChar)
                isLastChunk = endCharIx != -1
                if isLastChunk:
                    chunk = chunk[:endCharIx]
                data += chunk
                if isLastChunk:
                    break
            except:
                logger.reportException('Exception when waiting for incoming data.')
                try:
                    if not conn is None: conn.close()
                except:
                    logger.reportException('Could not close connection. Connection is discarded and process continues.')
                    pass
                return None, None
        return (data, conn)

    def sendString(self, string, encoding = 'utf8', endChar = chr(4)):
        # Encode the passed string to get raw bytes ready for transfer.
        bytes = string.encode(encoding)

        # Send that over socket.
        responseBytes = self.sendData(bytes, endChar.encode(encoding))

        # Decode the response string from raw bytes.
        return responseBytes.decode(encoding)

    def sendData(self, data, endSequence):
        """
        Sends raw bytes to the other end.
        data: bytes object that contains the data to send.
        endSequence: bytes object that represents the end sequence when sending/receiving data to/from the socket.
        """
        self._socket.sendall(data + endSequence)
        self._socket.settimeout(70)
        answer = self.waitForAnswer(endSequence)
        return answer

    def waitForStringAnswer(self, encoding = 'utf8', endChar = chr(4)):
        # Send that over socket.
        responseBytes = self.waitForAnswer(endChar.encode(encoding))

        # Decode the response string from raw bytes.
        return responseBytes.decode(encoding)

    def waitForAnswer(self, endSequence):
        answer = b''
        while True:
            chunk = self._socket.recv(4096)
            answer += chunk
            if not chunk or chunk[len(chunk)-len(endSequence):] == endSequence:
                break
        return answer
