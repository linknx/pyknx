==============================
Pyknx: Python bindings for KNX
==============================
-------------------------------
Pure python modules and scripts
-------------------------------

Copyright (C) 2012-2014 Cyrille Defranoux

----------------------------------------------------------------------

Python Version Requirement
==========================

Pyknx version 1 was compatible with Python 2 only. It was not compatible with Python 3 at all.
Pyknx version 2 is designed to work with a Python 3 environment. The main reason for this requirement is to benefit from unicode string enhancements in Python 3. Do not attempt to use it with Python 2 or you will likely get errors about ascii codec not being able to encode some characters. 

Upgrade Notice
==============

Version 2 of Pyknx consists in a rework of all standalone scripts to improve their usability. Pyknx has also been modified to embed acceptance tests. The overall API of the package has been slightly changed. Unless you were using the pyknx*.py standalone scripts of Pyknx version 1, upgrading to version 2 should be seamless. But please note that version 2 is still in beta phase and may thus not completely work as expected. Things should settle down quite soon but in the meantime, you may consider using the latest version of Pyknx 1.
As usual, feedback regarding version 2 is greatly appreciated.

What is it?
===========

Pyknx is a package that is aimed at providing basic functionality related to communicating with a Linknx instance. Pyknx provides python modules and scripts to:
- read or change value of linknx objects or execute linknx actions from the command line or from another Python application. See the section about [standalone scripts below](https://github.com/2franix/pyknx#contents-of-the-package) if you are searching for an easy way to get or change value of objects from a bash script, for instance.
- make a Python application be notified whenever some linknx objects change. This tutorial is mostly devoted to guiding the user through the steps required to make an app react on linknx objects' events.

To illustrate the communication between linknx and a python app using Pyknx, let's see what can be achieved with some examples.
First, let's output the value of some objects:

	from pyknx import linknx
	server = linknx.Linknx() # Connect to localhost:1028

	# Print status of all lights. The regex assumes that all lights objects are prefixed with 'Lights'.
	for lightObj in server.getObjects('Lights.*'): 
		print '{0} is currently {1}'.format(lightObj.id, lightObj.value)

For better performance, the snippet above can be rewritten like this since version 2.0.1:

	from pyknx import linknx
	server = linknx.Linknx() # Connect to localhost:1028

	# Print status of all lights. The regex assumes that all lights objects are prefixed with 'Lights'.
	lightObjects = server.getObjects('Lights.*')
	for lightObj, value in lightObjects.getValues().items(): # getValues gets all values with a single request to Linknx!
		print '{0} is currently {1}'.format(lightObj.id, value)

In these samples, there is no configuration required. Simply copy and paste them in a python script and it should work (pay attention to linknx hostname and port if you do not use default ones).
The example below shows how to implement a function that can be called each time the value of an object change. The module that provides the function *onLightsChanged* runs in the context of a *Pyknx communicator* which makes it run as a daemon. This allows to easily store data from one execution to another (see the *counters* global variable).

	counters = {}
	def onLightsChanged(context):
		global counters;
		if counters.has_key(context.objectId):
			counter[context.objectId] += 1
		else:
			counter[context.objectId] = 1

		print('Lights {0} have been switched {1} times.'.format(context.objectId, counter[context.objectId])

Refer to section [How does it work?](https://github.com/2franix/pyknx#how-does-it-work) to know how to configure your environment to make such magic happen. 

How does it work?
=================
Pyknx relies on the built-in **ioport communication** of Linknx. The principle is as following:

- edit your linknx XML configuration to **add a pyknxcallback attribute** to each object for which you would like a python callback to be called whenever its value changes. The value of the attribute corresponds to the name of the function to call:

``` xml
	<object gad="0/1/2" id="KitchenLights" type="1.001" pyknxcallback="onLightsChanged">Kitchen Lights</object>
```

- **use pyknxconf.py** to automatically append to the linknx XML configuration rules that are required for the communication to work. These rules use ioport actions to send data to the Python daemon but you don't have to mess with that if you are not willing to::

> pyknxconf.py -i linknx.xml -o patchedlinknx.xml

 See pyknxconf.py --help for a complete list of options. This command will declare the ioport and a few rules that are necessary for the communication to work. In the output xml file, you should read::

``` xml
	<ioport host="127.0.0.1" id="pyknx" port="1029" type="tcp"/>
```

- start Linknx with the above configuration::

> linknx --config=patchedlinknx.xml

- start an instance of the communicator using **pyknxcommunicator.py**. The name of a file of your own that implements every function declared with pyknxcallback attributes shall be **passed to the command line**::

> pyknxcommunicator.py -f myuserfile.py

And that's all. Every callback is passed a 'Context' instance that implements an **'object' property** which can be used to identify the object that is the source of the event on Linknx's side. Simply write 'context.object.value' to retrieve or change the value of the object.

Use several communicators with the same linknx instance
=======================================================
This is definitely advanced usage but if you happen to need several Pyknx communicator instances connected to the same Linknx instance, you will have to assign non-default names to your communicators (or at least, leave at most one communicator with the default name "pyknx").

By default, the communicator is named "pyknx", which makes pyknxconf.py search for "pyknxcallback" attributes in the configuration file for Linknx and generate "pyknx[ObjectId]" rules in this same configuration. "pyknx" is also the name assigned to the Linknx ioport used by Linknx to notify the communicator of events.

Thankfully, pyknxconf.py allows to change this default name, by means of its "-n" argument:

`pyknxconf.py -n mycustomname -i linknx.xml -o patchedlinknx.xml`

This will produce quite the same result as described above, except that pyknxconf.py will only take attributes named "customnamecallback" attributes into account. If an object is of interest for several communicators, specify as many "xxxxcallback" attributes as related communicators.

Initialize and dispose of the user script
======================================
The Pyknx communicator automatically calls some user script's callbacks if they are defined:
- initializeUserScript(context) is called when the communicator is initialized and ready to go
- finalizeUserScript(context) is called when the communicator is being stopped. At this time, Linknx is still able to raise object change events.
- endUserScript(context) is called when the communicator has fully stopped and has disconnected from the Linknx instance.

Contents of the package
=======================
The archive comes with a package named pyknx that offers the following pure-python modules:

- **linknx.py**: common module that implements the communication with a linknx server. With this module, one can retrieve linknx objects, read or write their value, read linknx configuration, ...
- **communicator.py**: this module contains the Communicator daemon, whose purpose is to receive events from linknx, through ioports.  It is then easy to write callbacks to react to object modifications. Additional scripts based on pyknx are provided (see below) in order to make this bidirectional communication with linknx just a few keystrokes away from now!
- logger.py: internal module that provides logging functionality for the package.
- tcpsocket.py: an internal module that implements common functionality related to socket communication. The end-user is unlikely to use this module directly.

This package also provides **additional python scripts** that are intended to run as standalone executables. They are briefly explained in the sections above but the --help argument of each script should be enough to help you understand how it really works.

- **pyknxconf.py** is used to automatically patch your linknx XML configuration in order to generate the ioport service and the rules necessary for the communication between Linknx and the Python daemon to work.
- **pyknxcommunicator.py** is the script that represents **the daemon** itself. Simply tell it where to find your user-defined python file with your implementation and it should work.
- **pyknxcall.py** can be used to ask the daemon to **perform a function call**. For instance 'pyknxcall.py -amyArgument=2 myCallback' should call the function myCallback(context) in your user-defined file. The passed context will contain a property named myArgument whose value is 2. This utility script is useful to help making external applications pass data to your daemon.
- **pyknxread.py** is used to read one or multiple object values at once. Regular expressions are supported. This script is a must-have to develop more complex shell scripts involving interactions with linknx, for instance.
- **pyknxwrite.py** is used to change one object's value.
- **pyknxexecute.py** is used to send an XML-formatted action to linknx. See linknx documentation to learn more about the syntax to use.
- **pyknxclient.py** is a deprecated client script that is able to read or write object values from/to linknx. This script has been split into pyknxread.py, pyknxwrite.py and pyknxexecute.py and is left in the package for compatibility. But please be aware that the three new atomic scripts are more convenient and more powerful to use and that pyknxclient.py may be removed in future versions of Pyknx.

How to install
==============
Two standard ways: using pip or calling setup.py manually.
With pip for Python 3 (http://www.pip-installer.org), simply do::

> pip3 install pyknx

You can optionally add --install-option="--user" to tell setup.py to install in your home rather than in one of the system-wide locations.

The other way: uncompress archive. Then calling setup.py directly boils down to::

> python setup.py install

You can optionally add --user to install in your home.
Please refer to distutils documentation for further details.

Why Pyknx?
==========

There is no doubt that Linknx is a very powerful, stable and simple-to-configure solution. It is sufficient for most needs in the frame of home automation. Nevertheless, as a developer, I sometimes find frustrating not having the opportunity to replace a set of XML rules in my Linknx config by a piece of code...

I first wrote a simple python script called lwknxclient whose unique functionality is to read/write Linknx object's values. This script solved the problem of easily sending data to Linknx from a bash script.

Then, my requirements evolved drastically as I wanted to implement my own alarm system to protect my home. I have a few door switches, cameras and smoke detectors that I wanted to use. I first implemented a simple version in pure XML that worked but it had many drawbacks:

- the configuration is quite verbose. This is the very nature of XML. Factorization is hardly ever possible.
- the configuration is tricky to test. I had to test it interactively after each modification. I quickly reached a point from which I was too afraid breaking something to add new functionality to my system.
- I had to rely on bash scripts for each non-trivial action executed by Linknx, which led to a bunch of scripts disseminated to various places on my server. Difficult to maintain too... And, no offense, but I have to respectfully admit that bash is not the kind of language I am happy to work with.
- calling external scripts from within shell-cmd actions has a major drawback: the script's lifetime is equal to the action's one. If the script has to retain some variables between two executions, it has no solution but polluting Linknx objects pool or storing data to files. None of these are convenient for a non-trivial application.

The answer to those problems was to implement a daemon in Python that manages my alarm system. This alarm system is available as the Homewatcher package: https://pypi.python.org/pypi/homewatcher/

License
=======
Pyknx is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pyknx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

For the full version of the GNU General Public License, please refer to http://www.gnu.org/licenses/.

Feel free to contact me by email (knx at aminate dot net) for feature requests or bug reports or simply to let me know whether you find this package useful or terribly useless! User feedback is never a waste of time.

Changelog
==========
1.0.0
-----
First version. This corresponds to a version that has been thoroughly tested with my own alarm system implemented in Python and with unit tests.

Until 1.0.8
------------
Minor changes, mainly in documentation. A few bugfixes.

1.0.9
-----
Added a "flags" member of pyknx.linknx.ObjectConfig, that contains the actual flags of the object as defined in the XML. If no attribute is set, this member is equal to 'cwtu'.
Changed behaviour for the "init" member: is now set to 'request' whenever the attribute is absent from XML. This is for consistency with respect to "flags".

1.0.10
------
Fixed a bug in tcpsocket.py: an import of pyknx.logger was missing and caused a crash when attempting to handle the exception thrown while waiting for incoming data.

1.0.11
------
Fixed a bug in Object.value for objects of type 'float'. The returned value was a string (the raw value sent by linknx). It is now a float as expected.

1.0.12
------
Changed the encoding of the output file generated by pyknxconf.py to ISO-8859-1 (aka latin-1) because other encodings are not well supported by linknx. (WARNING: this change has been reverted in next version)
Added a XML header that specifies the encoding used when sending a request to linknx. This encoding is <?xml version="1.0" encoding="ISO-8859-1"?>. If you encounter encoding problems, make sure that your linknx XML config file is encoded in either ascii or latin-1, not in utf-8 (for instance). I am currently working on a version 2 of pyknx that will rely on Python 3, which version of Python does no more suffer from the encoding issues of older versions.

1.0.13
------
Reverted changes regarding encoding implemented in 1.0.12. It appeared that it was not a good fix. Linknx had to handle utf8 request properly, so that clients can communicate with it in UTF8 too. Knxweb uses UTF8 and it was not an option to change that. A patch has been submitted to linknx's maintainer to fix that. Before that patch is integrated, it is very likely that v1.0.13 of pyknx will work nicely with most configurations, because encoding issues appear in rare cases.

1.0.14
------
Fixed a minor bug in configurator.py (which impacts pyknxconf.py): passing a communicator address that specifies the host by a name rather than by IP address was leading to a configuration incompatible with linknx. Linknx uses pth_connect and this function does not support named hosts. Added a conversion with socket.gethostbyname() in order to be sure to write the host's IP into the patched configuration.

2.0.0b7
-------
Reworked standalone scripts (pyknxconf, pyknxclient=>(pyknxread, pyknxwrite, pyknxexecute), pyknxcall) to increase ease of use and consistency:
- for instance, pyknxread can now read several object at once
- replaced argument parsing previously done with getopt by argparse that appears to be more efficient.
These breaking changes cause backward incompatibility for clients of these scripts. Please refer to the documentation of these script to learn more about their updated usage.

2.0.0b8
-------
Fixed an issue in the deprecated pyknxclient.py which was not working anymore with -R option.

2.0.0b9
-------
Fixed two issues related to executing actions with <execute/> requests:
- if the action is not trivial, linknx may need some time to complete it. In that case, it returns an intermediary status that is "ongoing", which was not expected by pyknx. That was leading to erroneous "failed" actions.
- because actions can take some time (if it is not trivial, linknx will not return before 1s), a need for asynchronous message arose. This functionality has been implemented and executeAction now returns immediately, without waiting for action's completion.

2.0.1
-----
Added the ability to get values for a collection of objects, rather than calling Object.value for each of them. Working on a collection does perform a single request for all objects.

2.1.0
-----
Added a version object to the package.
Implemented issue #2 to support datapoints 10 and 11 which represent date and time objects.

2.1.2
-----
Fixed some issues with the markdown README.

2.2.1
-----
Implemented [issue #3](https://github.com/2franix/pyknx/issues/3) to allow the connection of several communicators to the same Linknx instance. This introduces a breaking change documented in the Github issue's description. 

2.2.2
-----
Added Linknx.tryGetObject(self, objectId) to get an optional object without raising an exception if not found.

2.3.0
-----
Modified the behaviour of pyknxread.py to have it sort the results by object id. This makes the output more predictable.

2.3.1
-----
Fixed [issue #6](https://github.com/2franix/pyknx/issues/6) to make samples from this documentation work.
