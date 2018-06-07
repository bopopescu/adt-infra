"""AVD Launch test.

Verify the emulator launched in AVD can be detected.

usage: launch_avd.py [-h] [-t TIMEOUT_IN_SECONDS] --avd AVD
                     [--exec EMULATOR_EXEC]
"""

import logging
import os
import sys
import unittest


from emu_test.utils import emu_argparser
from emu_test.utils.emu_testcase import EmuBaseTestCase, AVDConfig, create_test_case_from_file

log = logging.getLogger('launch_avd')


class LaunchAVDTest(EmuBaseTestCase):
    def run_launch_avd_test(self, avd_config):
        """
        Run the Launch AVD test.
        """
        self.avd_config = avd_config
        self.assertEqual(self.create_avd(avd_config), 0)
        self.launch_emu_and_wait(avd_config)

assert emu_argparser.emu_args.config_file is not None, "Config file must be provided."
create_test_case_from_file('launch_avd', LaunchAVDTest, LaunchAVDTest.run_launch_avd_test)

if __name__ == '__main__':
    os.environ["SHELL"] = "/bin/bash"
    emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
    print emu_argparser.emu_args
    sys.argv[1:] = emu_args.unittest_args
    unittest.main()