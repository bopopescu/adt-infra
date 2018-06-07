"""Class for PSQ Boot Tests"""
import os
import time
import psutil
import shutil
from emu_test.utils import emu_argparser
from emu_test.utils.emu_testcase import EmuBaseTestCase
from emu_test.utils.emu_error import *

class PsqBootTestCase(EmuBaseTestCase):
    def __init__(self, *args, **kwargs):
        super(PsqBootTestCase, self).__init__(*args, **kwargs)
        self.avd_config = None

    @classmethod
    def setUpClass(cls):
        super(PsqBootTestCase, cls).setUpClass()

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

    def boot_check(self, avd):
        real_expected_boot_time = emu_argparser.emu_args.expected_boot_time;
        if 'swiftshader' in str(avd):
            real_expected_boot_time = real_expected_boot_time + emu_argparser.emu_args.expected_boot_time;
        if 'arm' in str(avd):
            real_expected_boot_time = real_expected_boot_time + emu_argparser.emu_args.expected_boot_time;
        if 'mips' in str(avd):
            real_expected_boot_time = real_expected_boot_time + emu_argparser.emu_args.expected_boot_time;
        try:
            self.boot_time = self.launch_emu_and_wait(avd)
            self.m_logger.error('AVD %s, boot time: %s, expected time: %s', avd, self.boot_time, real_expected_boot_time)
            self.assertLessEqual(self.boot_time, real_expected_boot_time)
            return
        except TimeoutError:
            self.m_logger.error('AVD %s, time out, try one more time', avd)
        except :
            self.m_logger.error('AVD %s, exception, try one more time', avd)
        self.kill_emulator()
        self.boot_time = self.launch_emu_and_wait(avd)
        self.m_logger.error('2nd try AVD %s, boot time: %s, expected time: %s', avd, self.boot_time, real_expected_boot_time)
        self.assertLessEqual(self.boot_time, real_expected_boot_time)

    def run_boot_test(self, avd_config):
        self.avd_config = avd_config
        self.assertEqual(self.create_avd(avd_config), 0)
        self.boot_check(avd_config)
