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

from distutils.core import setup
import sys
import pyknx

if sys.version_info.major < 3:
    print('This package is compatible with Python 3 and above.')
    exit(4)

setup(name='pyknx',
      version=pyknx.__version__,
      description='Python bindings for Linknx',
      long_description=''.join(open('README').readlines()),
      author='Cyrille Defranoux',
      author_email='knx@aminate.net',
      maintainer='Cyrille Defranoux',
      maintainer_email='knx@aminate.net',
      license='GNU Public General License',
      url='https://github.com/2franix/pyknx/',
      packages=['pyknx'],
      data_files=[('.', ['README', 'README.md'])],
      scripts=['pyknxcommunicator.py', 'pyknxcall.py', 'pyknxread.py', 'pyknxwrite.py', 'pyknxexecute.py', 'pyknxclient.py', 'pyknxconf.py', 'pyknxversion.py'])
