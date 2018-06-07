#!/usr/bin/env python

"""
A simple testing framework for emulator using python's unit testing framework.

Type:

./dotest.py -h

for available options.
"""

import sys
import os
import unittest
import logging
import re
import time
import psutil
import traceback
from subprocess import PIPE, check_call, CalledProcessError

# Add parent directory to current module. Then, emu_test module is recognized.
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             os.pardir))
from emu_test.utils import emu_argparser
from emu_test.utils import emu_unittest
from emu_test.utils import path_utils

# Provides a regular expression for matching fail message
TIMEOUT_REGEX = re.compile(r"(^\d+)([smhd])?$")


def printResult(result):
    """
    Prints out the results of the emulator test into the logger.
    :param result: class python2.7.unittest.TextTestResult.
    """
    def getTestName(id):
        return id.rsplit('.', 1)[-1]
    print
    logging.getLogger().info("Test Summary")
    logging.getLogger().info("Run %d tests (%d fail, %d pass, %d xfail, %d xpass)",
                     result.testsRun, len(result.failures)+len(result.errors), len(result.passes),
           len(result.expectedFailures), len(result.unexpectedSuccesses))
    if len(result.errors) > 0 or len(result.failures) > 0:
        for x in result.errors:
            if x[1].splitlines()[-1] == "TimeoutError":
                logging.getLogger().info("TIMEOUT: %s", getTestName(x[0].id()))
            else:
                logging.getLogger().info("FAIL: %s", getTestName(x[0].id()))
        for x in result.failures:
            logging.getLogger().info("FAIL: %s", getTestName(x[0].id()))

    if len(result.passes) > 0:
        logging.getLogger().info('------------------------------------------------------')
    for x in result.passes:
        logging.getLogger().info("PASS: %s, boot time: %s", getTestName(x.id()), x.boot_time)

    if len(result.expectedFailures) > 0:
        logging.getLogger().info('------------------------------------------------------')
    for x in result.expectedFailures:
        logging.getLogger().info("Expected Failure: %s", getTestName(x[0].id()))

    if len(result.unexpectedSuccesses) > 0:
        logging.getLogger().info('------------------------------------------------------')
    for x in result.unexpectedSuccesses:
        logging.getLogger().info("Unexpected Success: %s", getTestName(x.id()))

    logging.getLogger().info('')
    logging.getLogger().info("Test successful - %s", result.wasSuccessful())


def setupLogger():
    """
    Create logging.getLogger() that will be used by test driver
    """
    log_formatter = logging.Formatter('%(message)s')
    file_name = 'main_%s.log' % time.strftime("%Y%m%d-%H%M%S")
    if emu_argparser.emu_args.session_dir is None:
        emu_argparser.emu_args.session_dir = time.strftime("%Y%m%d-%H%M%S")
    if not os.path.exists(emu_argparser.emu_args.session_dir):
        os.makedirs(emu_argparser.emu_args.session_dir)
    if emu_argparser.emu_args.test_dir is None:
        emu_argparser.emu_args.test_dir = 'testcase_%s' % time.strftime("%Y%m%d-%H%M%S")
    if not os.path.exists(emu_argparser.emu_args.test_dir):
        os.makedirs(os.path.join(emu_argparser.emu_args.session_dir,
                                 emu_argparser.emu_args.test_dir))

    file_handler = logging.FileHandler(os.path.join(emu_argparser.emu_args.session_dir,
                                                    emu_argparser.emu_args.test_dir,
                                                    file_name))
    file_handler.setFormatter(log_formatter)
    # Test summary goes to standard error, since we rely on stderr to parse test results in buildbot
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(log_formatter)

    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().setLevel(getattr(logging, emu_argparser.emu_args.loglevel.upper()))
    logging.getLogger().info("Logger created and active.")


def findSystemAVDs():
    """
    Find available AVDs in system.  Found my calling -list-avds on target emulator.
    """
    # avd is searched in the order of $ANDROID_AVD_HOME,$ANDROID_SDK_HOME/.android/avd and $HOME/.android/avd
    avd_list_proc = psutil.Popen([emu_argparser.emu_args.emulator_exec, "-list-avds"], stdout=PIPE, stderr=PIPE)
    (output, err) = avd_list_proc.communicate()
    logging.getLogger().debug(output)
    logging.getLogger().debug(err)
    avd_list = [x.strip() for x in output.splitlines()]
    logging.getLogger().info("Found %d AVDs - %s", len(avd_list), avd_list)
    return avd_list


if __name__ == '__main__':
    """
    Main Execution.  For the passed arguments (held in emu_argparser) perform the requested tests.
    We find our test cases by searching for the passed in --file_pattern from the script execution directory.
    For instance, for a boot test we search for files named test_boot.*py, which we will find under
    test_boot/boot_test.py.  So this testcase would be found and run.

    When testcases are finished, we manually kill the ADB server.  This ensures a couple things:
      1.  It ensures our next test is run with a fresh daemon.  We are not testing ADB in these tests.
      2.  It ensures we do not hold up Buildbot code by holding on to a child process, blocking slave return.
    """
    os.environ["SHELL"] = "/bin/bash"

    try:
        emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
        setupLogger()
        logging.getLogger().info(emu_argparser.emu_args)

        if emu_argparser.emu_args.avd_list is None:
            emu_argparser.emu_args.avd_list = findSystemAVDs()

        test_root_dir = os.path.dirname(os.path.realpath(__file__))
        emuSuite = unittest.TestLoader().discover(start_dir=test_root_dir, pattern=emu_argparser.emu_args.pattern)
        emuRunner = emu_unittest.EmuTextTestRunner(stream=sys.stdout)
        emuResult = emuRunner.run(emuSuite)
        printResult(emuResult)
    except Exception:
        print "Error in dotest.py : " + traceback.format_exc()
        
    # Always attempt to kill the adb server.  We are now done testing with it.
    try:
        adb_binary = path_utils.get_adb_binary()
        check_call([adb_binary, 'kill-server'], stdout=PIPE, stdin=PIPE)
    except CalledProcessError:
        print "Error shutting down adb.  Error: " + traceback.format_exc()
    sys.exit(not emuResult.wasSuccessful())
