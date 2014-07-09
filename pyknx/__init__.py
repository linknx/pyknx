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
Pyknx is a package that is aimed at providing basic functionality related to communicating with a Linknx instance. It should help in sending or receiving data to/from Linknx.

linknx.py: common module that implements the communication with a linknx server. With this module, one can retrieve linknx objects, read or write their value, read linknx configuration, ...
communicator.py: this module contains the Communicator daemon, whose purpose is to receive events from linknx, through ioports.  It is then easy to write callbacks to react to object modifications. Additional scripts based on pyknx are provided (see below) in order to make this bidirectional communication with linknx just a few keystrokes away from now!
logger.py: internal module that provides logging functionality for the package.
tcpsocket.py: an internal module that implements common functionality related to socket communication. The end-user is unlikely to use this module directly.
"""
__all__ = ['linknx', 'communicator']
