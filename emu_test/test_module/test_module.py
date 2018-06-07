"""Test the emulator module time"""

import os
import psutil
import re
import shutil
import threading
import time
import unittest

from subprocess import PIPE, STDOUT
from emu_test.utils.emu_error import *
from emu_test.utils.emu_testcase import EmuBaseTestCase, AVDConfig
import emu_test.utils.emu_argparser as emu_argparser
import emu_test.utils.emu_testcase


class ModuleTestCase(EmuBaseTestCase):
    '''An emulator test that runs a single cts module'''

    def __init__(self, *args, **kwargs):
        super(ModuleTestCase, self).__init__(*args, **kwargs)
        self.avd_config = None

    @classmethod
    def setUpClass(cls):
        super(ModuleTestCase, cls).setUpClass()

    def kill_emulator(self):
        self.m_logger.debug('First try - quit emulator by adb emu kill')
        kill_proc = psutil.Popen(["adb", "emu", "kill"])
        # check emulator process is terminated
        result = self.term_check(timeout=5)
        if not result:
            self.m_logger.debug('Second try - quit emulator by psutil')
            self.kill_proc_by_name(["emulator", "qemu-system"])
            result = self.term_check(timeout=10)
            self.m_logger.debug("term_check after psutil.kill - %s", result)
        return result

    def tearDown(self):
        result = self.kill_emulator()
        self.m_logger.info("Remove AVD inside of tear down")
        # avd should be found $HOME/.android/avd/
        avd_dir = os.path.join(os.path.expanduser('~'), '.android', 'avd')
        try:
            if result and self.start_proc:
                self.start_proc.wait()
            time.sleep(1)
            self.kill_proc_by_name(["crash-service", "adb"])
            os.remove(os.path.join(avd_dir, '%s.ini' % self.avd_config.name()))
            shutil.rmtree(os.path.join(avd_dir, '%s.avd' % self.avd_config.name()), ignore_errors=True)
        except Exception, e:
            self.m_logger.error("Error in cleanup - %r", e)
            pass

    def module_check(self, avd):
        result_re = re.compile(".*([0-9]+) passed, ([0-9]+) failed, ([0-9]+) not executed")

        self.launch_emu_and_wait(avd)
        exec_path = emu_argparser.emu_args.cts_dir + "/tools/cts-tradefed"
        module = emu_argparser.emu_args.cts_module
        cts_cmd = [exec_path, "run", "cts", "-m", module]
        vars = {'result_line': "",
                'cts_proc': None}

        def launch_in_thread():
            self.m_logger.info('launch: ' + ' '.join(cts_cmd))
            vars['cts_proc'] = psutil.Popen(cts_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
            lines_iterator = iter(vars['cts_proc'].stdout.readline, b"")
            for line in lines_iterator:
                line=line.strip()
                self.simple_logger.info(line)
                if re.match(result_re, line):
                    vars['result_line'] = line
                    self.m_logger.info("Send exit to cts_proc")
                    vars['cts_proc'].stdin.write('exit\n')

        self.m_logger.info('Launching cts-tradefed, cmd: %s', ' '.join(cts_cmd))
        t_launch = threading.Thread(target=launch_in_thread)
        t_launch.start()
        t_launch.join()
        self.kill_emulator()
        self.assertTrue(vars['result_line'] != "", "Unable to successfully execute the module")
        pass_count, fail_count, skip_count = re.match(result_re, vars['result_line']).groups()
        self.assertEqual(0, int(fail_count), vars['result_line'])
        self.assertEqual(0, int(skip_count), vars['result_line'])
        self.assertTrue(int(pass_count) > 0, vars['result_line'])

    def run_module_test(self, avd_config):
        self.avd_config = avd_config
        self.assertEqual(self.create_avd(avd_config), 0)
        self.module_check(avd_config)


emu_test.utils.emu_testcase.create_test_case_from_file("module", ModuleTestCase, ModuleTestCase.run_module_test)

if __name__ == '__main__':
    os.environ["SHELL"] = "/bin/bash"
    emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
    print emu_argparser.emu_args
    sys.argv[1:] = emu_args.unittest_args
    unittest.main()
