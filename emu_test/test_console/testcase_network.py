"""Tests for network-related commands."""

import unittest
import time
import inspect

import testcase_base
from utils import util

CMD_NETWORK_STATUS = 'network status\n'
CMD_NETWORK_SPEED_EDGE = 'network speed edge\n'
CMD_NETWORK_SPEED_GSM = 'network speed gsm\n'
CMD_NETWORK_SPEED_FULL = 'network speed full\n'

NETWORK_DOWNLOAD_SPEED_EDGE = '(57.8 KB/s)'
NETWORK_DOWNLOAD_SPEED_GSM = '(1.8 KB/s)'
NETWORK_DOWNLOAD_SPEED_FULL = '(0.0 KB/s)'

NETWORK_SPEED_EDGE = 'EDGE'
NETWORK_SPEED_GSM = 'GSM'
NETWORK_SPEED_FULL = 'FULL'

NETWORK_SPEED_ASSERT_MSG_PREFIX = 'Failed to set network speed to'

class NetworkTest(testcase_base.BaseConsoleTest):
  """Tests for network-related commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(NetworkTest, self).__init__(method_name)
    else:
      super(NetworkTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def test_set_network_speed(self):
    """Test for command: setting network speed.

    TT ID: 21ff15e0-e43d-47a0-b14a-365014e46a72
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: set network speed
    Verify:
      Success to set network speed.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])

    self._set_network_speed(CMD_NETWORK_SPEED_EDGE, NETWORK_SPEED_EDGE, NETWORK_DOWNLOAD_SPEED_EDGE)
    self._set_network_speed(CMD_NETWORK_SPEED_GSM, NETWORK_SPEED_GSM, NETWORK_DOWNLOAD_SPEED_GSM)
    self._set_network_speed(CMD_NETWORK_SPEED_FULL, NETWORK_SPEED_FULL, NETWORK_DOWNLOAD_SPEED_FULL)

  def _set_network_speed(self, command, speed, keyword):
    """Sets the network speed."""
    assert_msg = '%s %s' % (NETWORK_SPEED_ASSERT_MSG_PREFIX, keyword)

    is_cmd_successful = False
    for i in range(util.NUM_MAX_TRIALS):
      print ('Running: %s, retrieve %s speed %s, trial # %s'
             % (inspect.stack()[0][3], keyword, speed, str(i + 1)))

      output_network_display = self._get_network_speed(command)

      if util.OK in output_network_display:
        is_cmd_successful = True
      self.assert_cmd_successful(is_cmd_successful, assert_msg, False, '',
                                 'Pattern: \n%s' % util.OK, keyword)

      output_network_display = self._get_network_status()
      output_extracted = util.extract_field_from_output(output_network_display, 'bits/s ')

      is_cmd_successful = False
      if keyword in output_extracted:
        is_cmd_successful = True
      self.assert_cmd_successful(is_cmd_successful, assert_msg, False, '',
                                 'Pattern: \n%s' % speed, keyword)

      print '%s %s' % (output_network_display, output_extracted)

      print ('Test result: %s %s %s => %s'
             % (inspect.stack()[0][3], keyword, speed, str(is_cmd_successful)))

  def _get_network_speed(self, command):
    """Gets the console output for 'network speed <network speed>' command.

    Returns:
        output_network_status: The console output for 'network speed <network speed>' command.
    """
    self.telnet.write(command)
    time.sleep(util.CMD_WAIT_TIMEOUT_S)
    output_network_speed = util.parse_output(self.telnet)
    return output_network_speed

  def _get_network_status(self):
    """Gets the console output for 'network status' command.

    Returns:
        output_network_status: The console output for 'network status' command.
    """
    self.telnet.write(CMD_NETWORK_STATUS)
    time.sleep(util.CMD_WAIT_TIMEOUT_S)
    output_network_status = util.parse_output(self.telnet)
    return output_network_status


if __name__ == '__main__':
  print '======= NetworkTest ======='
  unittest.main()