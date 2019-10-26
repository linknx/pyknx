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

class Version(object):
    def __init__(self, major, minor, revision, maturityLevel='', maturationStep=None):
        if maturityLevel not in ('a', 'b', ''):
            raise Exception('Unknown maturity level.')
        self.major = major
        self.minor = minor
        self.revision = revision
        self.maturityLevel = maturityLevel
        self.maturationStep = maturationStep

        if self.isRelease != (self.maturationStep == None):
            raise Exception('A maturation step is expected if and only if not a release version.')

    @property
    def isRelease(self):
        return self.maturityLevel == ''

    @property
    def components(self):
        if self.maturityLevel == '':
            return [self.major, self.minor, self.revision]
        elif self.maturationStep == None:
            return [self.major, self.minor, self.revision, self.maturityLevel]
        else:
            return [self.major, self.minor, self.revision, self.maturityLevel, self.maturationStep]

    def __eq__(self, other):
        return self._compareWith(other, 0)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self._compareWith(other, 1)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other):
        return self._compareWith(other, -1)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def _compareWith(self, other, comparisonType):
        if other == None:
            return False

        selfComponents = self.components
        otherComponents = other.components

        if comparisonType == 0: # Equality.
            return selfComponents == otherComponents
        else:
            for i in range(min(len(selfComponents), len(otherComponents))):
                c1 = selfComponents[i]
                c2 = otherComponents[i]

                # Replace the empty maturity level with a 'r' that naturally
                # compares greater than 'a' or 'b'.
                if i == 3:
                    c1 = 'r' if c1 == '' else c1
                    c2 = 'r' if c2 == '' else c2
                if comparisonType == -1: # Lower than.
                    if c1 < c2: return True
                    elif c1 > c2: return False
                elif comparisonType == 1: # Greater than.
                    if c1 > c2: return True
                    elif c1 < c2: return False
                else:
                    raise Exception('Invalid comparison type.')

            # If we do not have the same component count on both sides, the
            # longest is assumed to be older than the other (1.2.3b1 is older
            # than 1.2.3)
            if comparisonType == -1:
                return len(selfComponents) > len(otherComponents)
            elif comparisonType == 1:
                return len(selfComponents) < len(otherComponents)

    def __repr__(self):
        if self.maturityLevel == '':
            return '{major}.{minor}.{revision}'.format(**vars(self))
        else:
            if self.maturationStep == None:
                return '{major}.{minor}.{revision}{maturityLevel}'.format(**vars(self))
            else:
                return '{major}.{minor}.{revision}{maturityLevel}{maturationStep}'.format(**vars(self))

version = Version(2, 3, 2)
__version__=str(version)

