"""Tests for gsm-related commands."""

import unittest
import time
import inspect

import testcase_base
from utils import util

CMD_GSM_STATUS = 'gsm status\n'

CMD_GSM_DATA_OFF = 'gsm data off\n'
CMD_GSM_DATA_ROAMING = 'gsm data roaming\n'
CMD_GSM_DATA_SEARCHING = 'gsm data searching\n'

GSM_DATA_OFF = 'unregistered'
GSM_DATA_ROAMING = 'roaming'
GSM_DATA_SEARCHING = 'searching'

GSM_DATA_ASSERT_MSG_PREFIX = 'Failed to set gsm data state to'

class GSMTest(testcase_base.BaseConsoleTest):
  """Tests for gsm-related commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(GSMTest, self).__init__(method_name)
    else:
      super(GSMTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def test_set_gsm_status(self):
    """Test for command: setting gsm data.

    TT ID: 5c8892ba-e458-427c-a21d-19758e376749
    Test steps:
      1. Launch an emulator avd.
      2. From command prompt, run: telnet localhost <port>.
      3. Copy the auth_token value from ~/.emulator_console_auth_token.
      4. Run: auth auth_token.
      5. Run: set gsm data and verify.
    Verify:
      Success to set gsm data.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])

    self._set_gsm_data(CMD_GSM_DATA_OFF, GSM_DATA_OFF)
    self._set_gsm_data(CMD_GSM_DATA_ROAMING, GSM_DATA_ROAMING)
    self._set_gsm_data(CMD_GSM_DATA_SEARCHING, GSM_DATA_SEARCHING)

  def _set_gsm_data(self, command, state):
    assert_msg = '%s %s' % (GSM_DATA_ASSERT_MSG_PREFIX, state)

    is_cmd_successful = False
    for i in range(util.NUM_MAX_TRIALS):
      print ('Running: %s, retrieve gsm state %s, trial # %s'
             % (inspect.stack()[0][3], state, str(i + 1)))

      output_gsm_display = self._get_gsm_data(command)

      if util.OK in output_gsm_display:
        is_cmd_successful = True
      self.assert_cmd_successful(is_cmd_successful, assert_msg, False, '',
                                 'Pattern: \n%s', state)

      output_gsm_display = self._get_gsm_status()
      output_extracted = util.extract_field_from_output(output_gsm_display, 'data state: ')

      is_cmd_successful = False
      if state in output_extracted:
        is_cmd_successful = True
      self.assert_cmd_successful(is_cmd_successful, assert_msg, False, '',
                                 'Pattern: \n%s', state)

      print '%s %s' % (output_gsm_display, output_extracted)

      print ('Test result: %s %s => %s'
             % (inspect.stack()[0][3], state, str(is_cmd_successful)))

  def _get_gsm_data(self, command):
    """Gets the console output for 'gsm data <gsm data>' command.

    Returns:
        output_gsm_data: The console output for 'gsm data <gsm data>' command.
    """
    self.telnet.write(command)
    time.sleep(util.CMD_WAIT_TIMEOUT_S)
    output_gsm_data = util.parse_output(self.telnet)
    return output_gsm_data


  def _get_gsm_status(self):
    """Gets the console output for 'gsm status' command.

    Returns:
        output_gsm_status: The console output for 'gsm status' command.
    """
    self.telnet.write(CMD_GSM_STATUS)
    time.sleep(util.CMD_WAIT_TIMEOUT_S)
    output_gsm_status = util.parse_output(self.telnet)
    return output_gsm_status

if __name__ == '__main__':
  print '======= GSMTest ======='
  unittest.main()