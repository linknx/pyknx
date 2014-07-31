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
Lightweight command line client for linknx. It is aimed at executing actions defined by a XML string. The action to execute is read from standard input unless the --action option is set.
Example of a valid action: <action type="set-value" id="kitchen_heating" value="comfort"/>. This string is passed as-is to linknx so refer to linknx\'s documentation for further details.
"""

from pyknx import client

if __name__ == '__main__':
    client.handleRequest('execute', __doc__)
