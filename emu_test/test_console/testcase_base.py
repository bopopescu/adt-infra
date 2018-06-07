"""This class is a parent class for all subordniate "testcase_" classes.

This class is a parent class for all subordniate "testcase_" classes such as
testcase_battery.py, testcase_call.py, testcase_event.py, and testcaes_port.py.
It uses telnetlib to connect to telnet in order to communicate with emulator.
There is some sync problem or potential bug in emualtor, particularly observable
when run on Windows machine:
(https://code.google.com/p/android/issues/detail?id=220171)
The issue was handled by giving timeout parameter to the read_until function
of python telnetlib and give wait time of 0.5 after each write onto the telnet
stream.
"""

import inspect
import sys
import unittest

from utils import util


class BaseConsoleTest(unittest.TestCase):
  """This is the base clase for fall console test."""

  def __init__(self, method_name=None, avd=None):
    if method_name:
      super(BaseConsoleTest, self).__init__(method_name)
    else:
      super(BaseConsoleTest, self).__init__()
    self.avd = avd

  def setUp(self):
    auth_token = util.get_auth_token()
    self.telnet = util.telnet_emulator()
    self.telnet.write('%s %s\n' % (util.AUTH, auth_token))
    util.wait_on_windows()
    if (not util.check_read_until(
        self.telnet.read_until(util.OK, util.TIMEOUT_S))):
      sys.exit(-1)

  def tearDown(self):
    util.exit_emulator_console(self.telnet)

  def assert_cmd_successful(self, is_cmd_successful, assertion_msg, has_status,
                            status, expected, actual):
    if has_status:
      print ('Test result: %s status matches %s => %s' %
             (inspect.stack()[0][3], status, str(is_cmd_successful)))
    else:
      print ('Test result: %s => %s' %
             (inspect.stack()[0][3], str(is_cmd_successful)))

    if not is_cmd_successful:
      print 'Expected output:'
      print expected
      print 'Actual Output:'
      print actual
    self.assertTrue(is_cmd_successful, assertion_msg)


if __name__ == '__main__':
  print '======= Base Console Test ======='
  unittest.main()
