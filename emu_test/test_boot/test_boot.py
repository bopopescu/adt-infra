"""Test the emulator boot time"""

import unittest
import os
import time
import psutil
import shutil
import traceback

from emu_test.utils.emu_error import *
from emu_test.utils.emu_argparser import emu_args
import emu_test.utils.emu_testcase
from emu_test.utils.emu_testcase import EmuBaseTestCase, AVDConfig
import emu_test.utils.path_utils as path_utils

class BootTestCase(EmuBaseTestCase):
    def __init__(self, *args, **kwargs):
        super(BootTestCase, self).__init__(*args, **kwargs)
        self.avd_config = None
    @classmethod
    def setUpClass(cls):
        super(BootTestCase, cls).setUpClass()

    def kill_emulator(self):
        self.m_logger.debug('First try - quit emulator by adb emu kill')
        adb_binary = path_utils.get_adb_binary()
        kill_proc = psutil.Popen([adb_binary, "emu", "kill"]).communicate()
        # check emulator process is terminated
        result = self.term_check(timeout=5)
        if not result:
            self.m_logger.info('Second try - quit emulator by psutil')
            self.kill_proc_by_name(["emulator", "qemu-system"])
            result = self.term_check(timeout=10)
            self.m_logger.info("term_check after psutil.kill - %s" % result)
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
            self.m_logger.error("Error in cleanup - %r" % e)
            pass

    def boot_check(self, avd):
        real_expected_boot_time = emu_args.expected_boot_time
        if 'swiftshader' in str(avd):
            real_expected_boot_time = real_expected_boot_time + emu_args.expected_boot_time
        if 'arm' in str(avd):
            real_expected_boot_time = real_expected_boot_time + emu_args.expected_boot_time
        if 'mips' in str(avd):
            real_expected_boot_time = real_expected_boot_time + emu_args.expected_boot_time
        try:
            self.boot_time = self.launch_emu_and_wait(avd)
            self.m_logger.error('AVD %s, boot time: %s, expected time: %s'
                                % (avd, self.boot_time, real_expected_boot_time))
            self.assertLessEqual(self.boot_time, real_expected_boot_time)
            return
        except TimeoutError:
            self.m_logger.error('AVD %s, time out, try one more time' % str(avd))
        except:
            self.m_logger.error('AVD %s, exception, try one more time' % str(avd))
            self.m_logger.error(traceback.format_exc())
        self.kill_emulator()
        self.boot_time = self.launch_emu_and_wait(avd)
        self.m_logger.error('2nd try AVD %s, boot time: %s, expected time: %s'
                            % (avd, self.boot_time, real_expected_boot_time))
        self.assertLessEqual(self.boot_time, real_expected_boot_time)

    def run_boot_test(self, avd_config):
        self.avd_config = avd_config
        if self.create_avd(avd_config) == 0:
            self.boot_check(avd_config)


def create_test_case_for_avds():
    avd_list = emu_args.avd_list
    for avd in avd_list:
        def fn(i):
            return lambda self: self.boot_check(i)
        setattr(BootTestCase, "test_boot_%s" % avd, fn(avd))

if emu_args.config_file is None:
    create_test_case_for_avds()
else:
    emu_test.utils.emu_testcase.create_test_case_from_file("boot", BootTestCase, BootTestCase.run_boot_test)

if __name__ == '__main__':
    os.environ["SHELL"] = "/bin/bash"
    emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
    print emu_argparser.emu_args
    sys.argv[1:] = emu_args.unittest_args
    unittest.main()
