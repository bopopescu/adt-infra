"""This class is the entry point for console tests from dotest.py.

When the class is instantiated, it sets up logger and runs emulator for tests.
Then, using unittest loader, it loads all the console test cases
that are written in the python files with filename starting with "testcase_"
in the same directory.
"""

import glob
import importlib
import inspect
import os
import shutil
import subprocess
import sys
import time
import unittest
import xml.etree.ElementTree as ET

import psutil

import emu_test
from emu_test.utils import emu_argparser
from emu_test.utils import emu_testcase
from emu_test.utils import emu_unittest
from emu_test.utils import path_utils
from utils import util

try:
    from subunit import run as subunit_run
except ImportError:
    subunit_run = None


CUR_DIR = os.path.dirname(os.path.realpath(__file__))
CONSOLE_RESULT_XML_FILE = 'consoleTestResult.xml'
CONSOLE_CSS_FILE = os.path.join(CUR_DIR, 'static', 'console.css')
CONSOLE_XSL_FILE = os.path.join(CUR_DIR, 'static', 'console.xsl')

g_xml_string_result = ''
g_avd_counter = 0


class ConsoleTestCase(emu_testcase.EmuBaseTestCase):
    """This class helps for run all console tests."""

    def __init__(self, *args, **kwargs):
        super(ConsoleTestCase, self).__init__(*args, **kwargs)
        self.avd_config = None

    @classmethod
    def setUpClass(cls):
        super(ConsoleTestCase, cls).setUpClass()

    def kill_emulator(self):
        self.m_logger.debug('First try - quit emulator by adb emu kill')
        adb_binary = path_utils.get_adb_binary()
        kill_proc = psutil.Popen([adb_binary, "emu", "kill"]).communicate()
        # Check emulator process is terminated
        result = self.term_check(timeout=5)
        if not result:
            self.m_logger.info('Second try - quit emulator by psutil')
            self.kill_proc_by_name(["emulator", "qemu-system"])
            result = self.term_check(timeout=10)
            self.m_logger.info("term_check after psutil.kill - %s" % result)
        return result

    def tearDown(self):
        result = self.kill_emulator()
        self.m_logger.info('Remove AVD inside of tear down')
        # avd should be found $HOME/.android/avd/
        avd_dir = os.path.join(os.path.expanduser('~'), '.android', 'avd')
        try:
            if result and self.start_proc:
                self.start_proc.wait()
            time.sleep(1)
            self.kill_proc_by_name(['crash-service' 'adb'])
            os.remove(os.path.join(avd_dir, '%s.ini' % self.avd_config.name()))
            shutil.rmtree(os.path.join(avd_dir, '%s.avd' % self.avd_config.name()), ignore_errors=True)
        except Exception, e:
            self.m_logger.error('Error in cleanup - %r' % e)
            pass

    def get_test_name(self, failed_test_id):
        return failed_test_id.rsplit('.', 1)[-1]

    def create_result_xml(self, emu_result):
        global g_xml_string_result
        global g_avd_counter
        g_avd_counter += 1

        dst_path = os.path.join(emu_argparser.emu_args.session_dir,
                                emu_argparser.emu_args.test_dir,
                                CONSOLE_RESULT_XML_FILE)
        xsl_path = os.path.join(emu_argparser.emu_args.session_dir,
                                emu_argparser.emu_args.test_dir,
                                'console.xsl')
        css_path = os.path.join(emu_argparser.emu_args.session_dir,
                                emu_argparser.emu_args.test_dir,
                                'console.css')

        if os.name == util.WINDOWS_OS_NAME:
            subprocess.call(['copy', CONSOLE_XSL_FILE, xsl_path], shell=True)
            subprocess.call(['copy', CONSOLE_CSS_FILE, css_path], shell=True)
        else:
            subprocess.call(['cp', CONSOLE_XSL_FILE, xsl_path])
            subprocess.call(['cp', CONSOLE_CSS_FILE, css_path])

        result = ET.Element('result')

        # The avdCounter tag is used for indexing.
        ET.SubElement(result, 'avdCounter', value=str(g_avd_counter))

        ET.SubElement(result, 'testMethodName', name=self._testMethodName)
        ET.SubElement(result, 'avdConfigName', name=self.avd_config.name())

        result_summary = ET.SubElement(result, 'resultSummary')
        ET.SubElement(result_summary, 'total', num=str(emu_result.testsRun))
        ET.SubElement(result_summary, 'passes', num=str(len(emu_result.passes)))
        ET.SubElement(result_summary, 'failures',
                      num=str(len(emu_result.failures)))
        ET.SubElement(result_summary, 'errors', num=str(len(emu_result.errors)))
        ET.SubElement(result_summary, 'expectedFailures',
                      num=str(len(emu_result.expectedFailures)))
        ET.SubElement(result_summary, 'unexpectedSuccesses',
                      num=str(len(emu_result.unexpectedSuccesses)))

        passes = ET.SubElement(result, 'Passes')
        for x in emu_result.passes:
            ET.SubElement(passes, 'test', name=self.get_test_name(x.id()),
                          test_result='pass')

        failures = ET.SubElement(result, 'Failures')
        for x in emu_result.failures:
            ET.SubElement(failures, 'test', name=self.get_test_name(x[0].id()),
                          test_result='fail')

        errors = ET.SubElement(result, 'Errors')
        for x in emu_result.errors:
            ET.SubElement(errors, 'test', name=self.get_test_name(x[0].id()),
                          test_result='error')

        expected_failures = ET.SubElement(result, 'ExpectedFailures')
        for x in emu_result.expectedFailures:
            ET.SubElement(expected_failures, 'test',
                          name=self.get_test_name(x[0].id()),
                          test_result='expected failure')

        unexpected_successes = ET.SubElement(result, 'UnexpectedSuccesses')
        for x in emu_result.unexpectedSuccesses:
            ET.SubElement(unexpected_successes, 'test',
                          name=self.get_test_name(x.id()),
                          test_result='unexpected failure')

        xml_string_result = ET.tostring(result)
        # Saves each avd testing result to global variable: g_xml_string_result
        g_xml_string_result += xml_string_result

        # Refresh the current whole test result page.
        with open(dst_path, 'w+') as modified:
            modified.write(('<?xml-stylesheet type="text/xsl" '
                            'href="console.xsl"?>\n<avd>%s</avd>'
                            % g_xml_string_result))
            self.m_logger.info("Wrote %s" % dst_path)

    def print_console_result(self, emu_result):
        self.m_logger.info(
            'Run %d tests (%d fail, %d pass, %d xfail, %d xpass)' %
            (emu_result.testsRun,
             len(emu_result.failures) + len(emu_result.errors),
             len(emu_result.passes),
             len(emu_result.expectedFailures),
             len(emu_result.unexpectedSuccesses)))

        border_line = '------------------------------------------------------'
        if emu_result.passes:
            self.m_logger.info(border_line)
        for x in emu_result.passes:
            self.m_logger.info('PASS: %s' % self.get_test_name(x.id()))

        if len(emu_result.failures) + len(emu_result.errors) > 0:
            self.m_logger.info(border_line)
        for x in emu_result.failures:
            self.m_logger.info('Failure: %s' % self.get_test_name(x[0].id()))
        for x in emu_result.errors:
            self.m_logger.info('Error: %s' % self.get_test_name(x[0].id()))

        if emu_result.expectedFailures:
            self.m_logger.info(border_line)
        for x in emu_result.expectedFailures:
            self.m_logger.info('Expected Failure: %s' %
                               self.get_test_name(x[0].id()))

        if emu_result.unexpectedSuccesses:
            self.m_logger.info(border_line)
        for x in emu_result.unexpectedSuccesses:
            self.m_logger.info('Unexpected Success: %s' %
                               self.get_test_name(x.id()))

        self.m_logger.info('')
        self.create_result_xml(emu_result)

    def get_all_console_test_classes(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))

        test_classes = []
        for test_file in glob.glob(os.path.join(current_dir, 'testcase_*.py')):
            name = os.path.splitext(os.path.basename(test_file))[0]
            test_module = importlib.import_module('.' + name, 'test_console')
            for member in dir(test_module):
                handler_class = getattr(test_module, member)
                if handler_class and inspect.isclass(handler_class):
                    test_classes.append(handler_class)

        return test_classes

    def console_test_check(self, avd, builder_name):
        """Checks console test.

        1) Run emulator with self.launch_emu_and_wait(avd)
        2) Print to logger that the test begins
        3) Load all the console tests using unittest.TestLoader()
        4) Verify whether every individual testcase was successful

        Args:
          avd: The running avd.
        """
        self.launch_emu_and_wait(avd)
        self.m_logger.info('Console tests (%s) start.' % self._testMethodName)

        test_classes = self.get_all_console_test_classes()
        emu_suite = unittest.TestSuite()
        for test_class in test_classes:
            for method in dir(test_class):
                if method.startswith('test_'):
                    emu_suite.addTest(test_class(method, avd, builder_name))

        # The fact that we have a single test case that in turn runs
        # multiple other test cases makes it difficult to have a clean
        # approach. Fixtures may be used at some point.
        subunit_file = getattr(emu_argparser.emu_args, "subunit_file", None)
        if subunit_file:
            self.m_logger.info("Streaming subunit results to %s.",
                               subunit_file)
            with open(subunit_file, 'ab') as stream:
                emu_runner = subunit_run.SubunitTestRunner(stream=stream)
                emu_result = emu_runner.run(emu_suite)
        else:
            emu_runner = emu_unittest.EmuTextTestRunner(stream=sys.stdout)
            emu_result = emu_runner.run(emu_suite)
            self.print_console_result(emu_result)

        self.assertTrue(emu_result.wasSuccessful(),
                        '%s was failed.' % self._testMethodName)

    def run_console_test(self, avd_config, builder_name):
        """Run console test.

        Run console test with the given avd_config.
        This function first make sure whether avd is properly up or not.

        Args:
          avd_config: The avd configuration.
        """
        self.avd_config = avd_config
        self.assertEqual(self.create_avd(avd_config), 0)
        self.console_test_check(avd_config, builder_name)


if emu_argparser.emu_args.config_file is None:
    sys.exit(-1)
else:
    emu_test.utils.emu_testcase.create_test_case_from_file(
        'console', ConsoleTestCase, ConsoleTestCase.run_console_test)

if __name__ == '__main__':
    os.environ['SHELL'] = '/bin/bash'
    emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
    print emu_argparser.emu_args
    sys.argv[1:] = emu_argparser.emu_args.unittest_args
    unittest.main()
