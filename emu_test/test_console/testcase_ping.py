"""Tests for the ping command."""

import inspect
import time
import unittest

import testcase_base
from utils import util

CMD_PING = 'ping\n'
PING_RESPONSE = 'I am alive!.*\nOK'



class PingTest(testcase_base.BaseConsoleTest):
  """Tests for the ping command."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(PingTest, self).__init__(method_name)
    else:
      super(PingTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _execute_command_and_verify(self, command, expected_output, assert_msg):
    """Executes console command and verify output.

    Args:
        command: Console command to be executed.
        expected_output: Expected console output.
        assert_msg: Assertion message.
    """
    is_command_successful, output = util.execute_console_command(
        self.telnet, command, expected_output)

    self.assert_cmd_successful(is_command_successful, assert_msg, False, '',
                               'Pattern:\n%s' % expected_output, output)

  def _auth_user_for_emulator_console(self):
    """Authorize user."""
    auth_token = util.get_auth_token()
    self.telnet = util.telnet_emulator()
    self.telnet.write('%s %s\n' % (util.AUTH, auth_token))
    util.wait_on_windows()
    if (not util.check_read_until(
        self.telnet.read_until(util.OK, util.TIMEOUT_S))):
      sys.exit(-1)

  def test_ping(self):
    """Test for command: ping

    Test Rail ID: ?
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: ping
      3. Verify 1
      4. Copy the auth_token value from ~/.emulator_console_auth_token
      5. Run: auth auth_token
      6. Run: ping
      7. Verify 1
    Verify:
      1. The ping response is displayed
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    assert_msg = 'Failed to properly display the ping response.'
    self._execute_command_and_verify(CMD_PING, PING_RESPONSE, assert_msg)
    self._auth_user_for_emulator_console()
    self._execute_command_and_verify(CMD_PING, PING_RESPONSE, assert_msg)

if __name__ == '__main__':
  print '======= Ping Test ======='
  unittest.main()
