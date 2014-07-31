#!/usr/bin/python3

# Copyright (C) 2014 Cyrille Defranoux
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
import os
import subprocess
import unittest
import time
import traceback
import inspect
import stat
import pwd, grp
import shutil
import tempfile
import importlib

from pyknx import logger, linknx, configurator, communicator
import logging

class AssertionsHandle(object):
    def __init__(self, test, assertions):
        self.test = test
        self.assertions = assertions

    def __enter__(self):
        self.test.currentAssertions.extend(self.assertions)

    def __exit__(self, exc_type, exc_value, traceback):
        for assertion in self.assertions:
            self.test.currentAssertions.remove(assertion)

class PatchHandle(object):
    def __init__(self, module, patches):
        self.module = module
        self.patches = patches
        self.originalMethodObjects = {}

    def __enter__(self):
        for k,v in self.patches.items():
            logger.reportDebug('Patching function object {0}.{1}={2}'.format(self.module, k, v))
            self.originalMethodObjects[k] = getattr(self.module, k)
            setattr(self.module, k, v)

    def __exit__(self, exc_type, exc_value, traceback):
        for k,v in self.originalMethodObjects.items():
            logger.reportDebug('Restoring function object {0}.{1}={2}'.format(self.module, k, v))
            setattr(self.module, k, v)

class TestCaseBase(unittest.TestCase):
    def setUp(self):
        self.name = self.id()[len(self.__module__) + 1:]
        logFile = 'test_files/{0}.log'.format(self.name)
        if os.path.exists(logFile):
            os.remove(logFile)
        logger.initLogger((logFile, logging.DEBUG), logging.INFO)
        logger.reportInfo('*******Start {0}*************'.format(self.name))
        self.currentAssertions = []
        self.pyknxScriptsDirectory = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.pyknxModulesDirectory = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

    def getCurrentTestName(self):
        tb = traceback.extract_stack()
        for file, lineNum, function, source in reversed(tb):
            if function.startswith('test'):
                return function

        raise Exception('No test function could be found.')

    def getResourceFullName(self, resourceSuffix, appendsTestName=True):
        return self._getFileFullName('resources', resourceSuffix, appendsTestName)

    def getOutputFullName(self, outputSuffix, appendsTestName=True):
        return self._getFileFullName('test_files', outputSuffix, appendsTestName)

    def _getFileFullName(self, directory, suffix, appendsTestName=True):
        prefix = self.getCurrentTestName() if appendsTestName else ''
        suffix = '{0}'.format(suffix) if suffix != None else ''
        separator = '.' if prefix and suffix else ''
        resourceFile = '{testClass}.{prefix}{sep}{suffix}'.format(testClass=self.__class__.__name__, prefix=prefix, suffix=suffix, sep=separator)
        moduleFile = importlib.import_module(self.__class__.__module__).__file__
        return os.path.join(os.path.dirname(moduleFile), directory, resourceFile)

    def waitDuring(self, duration, reason, assertions=[], assertStartMargin=0, assertEndMargin=0):
        self.assertTrue(duration >= 0, 'Duration is negative, is it intended?')
        self.waitUntil(time.time() + duration, reason, assertions, assertStartMargin, assertEndMargin)

    def waitUntil(self, endTime, reason, assertions=[], assertStartMargin=0, assertEndMargin=0):
        state = 0 # 0: undefined, 1: before assertions, 2: during assertions, 3: after assertions
        with AssertionsHandle(self, assertions):
            startTime = time.time()
            assertStart = startTime + assertStartMargin
            assertEnd = endTime - assertEndMargin
            while time.time() < endTime:
                currentTime = time.time()
                if currentTime < assertStart and assertStartMargin != 0:
                    newState = 1
                    status = 'before assertions'
                    duration = assertStart - currentTime
                elif currentTime > assertEnd and assertEndMargin != 0:
                    newState = 3
                    status = 'after assertions'
                    duration = endTime - currentTime
                else:
                    newState = 2
                    status = 'with assertions' if assertions else 'no assertions'
                    duration = assertEnd - currentTime

                # Notify progress.
                if newState != state:
                    state = newState
                    logger.reportInfo('{0} ({2}) (during {1} seconds)'.format(reason, round(duration, 1), status))

                # Check all pending assertions.
                for assertion in self.currentAssertions:
                    try:
                        if state == 2:
                            assertion()
                    except:
                        logger.reportInfo('Exception caught in waitUntil after {0}s'.format(time.time() - startTime))
                        raise

                # Sleep until optimal end of iteration.
                time.sleep(0.1)

    def assertShellCommand(self, command, expectedStdOut=None, expectedStdErr=None, expectedReturnCode=None, stdin=None):

        shouldSucceed = expectedStdErr == None and (expectedReturnCode == None or expectedReturnCode == 0)

        # Redirect command's stdout to a file so that we can compare with what
        # is expected.
        stdoutHandle, stdoutFilename = tempfile.mkstemp()
        stderrHandle, stderrFilename = tempfile.mkstemp()
        try:
            with open(stdoutFilename, 'w+') as stdoutFD:
                with open(stderrFilename, 'w+') as stderrFD:
                    returnCode = subprocess.call(command, stdout=stdoutFD, stderr=stderrFD, stdin=stdin)
                    if (returnCode == 0) != shouldSucceed:
                        logger.reportError('Command {command} output is {out}'.format(command=command, out=stdoutFD.readlines()))
                        logger.reportError('stderr is {out}'.format(out=stderrFD.readlines()))
                        self.fail('Command was expected to {failOrSucceed} but it {status}. Return code is {returnCode}'.format(failOrSucceed='succeed' if shouldSucceed else 'fail', status='succeeded' if returnCode == 0 else 'failed', returnCode=returnCode))

            # Compare output to what is expected.
            if expectedStdOut != None:
                self.assertFilesAreEqual(stdoutFilename, expectedStdOut)
            else:
                with open(stdoutFilename, 'r') as stdoutFD:
                    lines = stdoutFD.readlines()
                    self.assertEqual(os.stat(stdoutFilename).st_size, 0, 'No output was expected on standard output from this command. Output is {0}'.format(lines))
            if expectedStdErr != None:
                self.assertFilesAreEqual(stderrFilename, expectedStdErr)
            else:
                with open(stderrFilename, 'r') as stderrFD:
                    lines = stderrFD.readlines()
                    self.assertEqual(os.stat(stderrFilename).st_size, 0, 'No output was expected on standard error from this command. Output is {0}'.format(lines))

            if expectedReturnCode != None:
                self.assertEqual(returnCode, expectedReturnCode)

        finally:
            os.remove(stdoutFilename)
            os.remove(stderrFilename)

    def assertFilesAreEqual(self, file1, file2):
        lines1 = None
        lines2 = None
        if isinstance(file1, str):
            with open(file1) as f1:
                lines1 = f1.readlines()
        else:
            lines1 = file1.readlines()
        if isinstance(file2, str):
            with open(file2) as f2:
                lines2 = f2.readlines()
        else:
            lines2 = file2.readlines()

        self.assertEqual(len(lines1), len(lines2), 'Line count mismatch between files:\n{0}\n{1}'.format(file1, file2))
        for i in range(len(lines1)):
            line1 = lines1[i]
            line2 = lines2[i]
            # Do not take trailing \n, \t or whitespaces into account for the
            # last line.
            if i == len(lines1) - 1:
                line1 = line1.rstrip('\n\t ')
                line2 = line2.rstrip('\n\t ')
            self.assertEqual(line1, line2, 'Difference detected at line #{lineno} between {files})'.format(lineno=i+1, files=(file1, file2)))

    def assertFileRights(self, path, rights, owner=None, group=None, isStrict = False):
        fileStat = os.stat(path)

        # Check rights.
        if not rights is None:
            packedRights = 0
            if 'r' in rights[0]: packedRights |= stat.S_IRUSR
            if 'w' in rights[0]: packedRights |= stat.S_IWUSR
            if 'x' in rights[0]: packedRights |= stat.S_IXUSR
            if 'r' in rights[1]: packedRights |= stat.S_IRGRP
            if 'w' in rights[1]: packedRights |= stat.S_IWGRP
            if 'x' in rights[1]: packedRights |= stat.S_IXGRP
            if 'r' in rights[2]: packedRights |= stat.S_IROTH
            if 'w' in rights[2]: packedRights |= stat.S_IWOTH
            if 'x' in rights[2]: packedRights |= stat.S_IXOTH
            ugoRights = fileStat.st_mode & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            if isStrict:
                self.assertEqual(ugoRights, packedRights, 'File {0} does not hold the expected rights. Expected {1}, found {2}'.format(path, packedRights, ugoRights))
            else:
                self.assertNotEqual(ugoRights & packedRights, 0, 'File {0} does not hold the expected minimum rights. Expected {1}, found {2}'.format(path, packedRights, ugoRights))

        # Check ownership.
        if not owner is None:
            uid = pwd.getpwnam(owner).pw_uid
            self.assertEqual(fileStat.st_uid, uid, 'Wrong owner for {0}'.format(path))
        if not group is None:
            gid = grp.getgrnam(group).gr_gid
            self.assertEqual(fileStat.st_gid, gid, 'Wrong group for {0}'.format(path))

class WithLinknxTestCase(TestCaseBase):
    def setUp(self, linknxConfFile='linknx_test_conf.xml', communicatorAddr=('localhost', 1031), patchLinknxConfig=True, userScript='linknxuserfile.py', userScriptArgs=None):
        TestCaseBase.setUp(self)
        self.linknxProcess = None
        self.linknx = None
        self.communicator = None
        self.linknxOutputFDs = None
        self.linknxXMLConfig = linknxConfFile
        self.communicatorAddress = communicatorAddr
        try:

            # Patch config.
            if self.linknxXMLConfig != None:
                testDir = 'test_files'
                if not os.path.exists(testDir):
                    os.mkdir(testDir)
                if self.communicatorAddress != None and patchLinknxConfig:
                    linknxPatchedConfigFile = os.path.join(testDir, 'autogenlinknx.conf.xml')
                    if os.path.exists(linknxPatchedConfigFile):
                        os.remove(linknxPatchedConfigFile)
                    self.configurator = configurator.Configurator(self.linknxXMLConfig, linknxPatchedConfigFile, self.communicatorAddress, 'nondefaultprefixfortest')
                    self.configurator.cleanConfig()
                    self.configurator.generateConfig()
                    self.configurator.writeConfig()
                else:
                    linknxPatchedConfigFile = self.linknxXMLConfig

                # Start linknx.
                linknxErrFilename = 'test_files/{0}.linknx.err'.format(self.name)
                linknxOutFilename = 'test_files/{0}.linknx.out'.format(self.name)
                efdw = open(linknxErrFilename, 'w')
                efdr = open(linknxErrFilename, 'r')
                ofdw = open(linknxOutFilename, 'w')
                self.linknxOutputFDs = (efdr, efdw, ofdw)
                self.linknxProcess = subprocess.Popen( ['linknx', '--config={0}'.format(linknxPatchedConfigFile)], stdout=self.linknxOutputFDs[2], stderr=self.linknxOutputFDs[1])
                logger.reportInfo('linknx started with pid {0}'.format(self.linknxProcess.pid))
                self.linknx = linknx.Linknx('localhost', 1030)
                self.currentAssertions.append(self.checkLinknx)

            # Start pyknx.
            if self.communicatorAddress != None:
                self.communicator = communicator.Communicator(self.linknx, userScript, self.communicatorAddress, userScriptArgs)
                self.communicator.startListening()
            else:
                self.communicator = None

            logger.reportInfo('Set up finished.')
            self.waitDuring(0.5, 'Pause to make sure everything gets ready.')
        except:
            logger.reportException('Error in setUp.')
            self.tearDown()
            self.fail('Test setup failed.')
            raise

    def tearDown(self):
        logger.reportInfo('Tearing down...')

        logger.reportInfo('Stopping communicator...')
        if self.communicator: self.communicator.stopListening()
        logger.reportInfo('communicator is stopped.')
        if self.linknxProcess: self.linknxProcess.kill()
        logger.reportInfo('linknx is stopped.')
        if self.linknxOutputFDs:
            self.linknxOutputFDs[0].close()
            self.linknxOutputFDs[1].close()
            self.linknxOutputFDs[2].close()

        TestCaseBase.tearDown(self)

        logger.reportInfo('*******End of {0}*************\n\n\n'.format(self.name))

    def checkLinknx(self):
        # Check linknx is running.
        self.assertIsNotNone(self.linknxProcess, 'No linknx process.')
        self.assertIsNone(self.linknxProcess.returncode, 'Unexpected linknx termination.')

        # Linknx's should not output errors.
        if self.linknxOutputFDs:
            self.linknxOutputFDs[0].seek(0)
            errorLine = self.linknxOutputFDs[0].readline()
            if errorLine:
                self.assertFalse(errorLine, 'Linknx outputs an error: {0}'.format(errorLine))

    def patchUserModule(self, patches):
        return PatchHandle(self.communicator._userModule, patches)
