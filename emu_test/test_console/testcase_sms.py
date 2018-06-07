"""Tests for sms-related commands."""

import inspect
import json
import os
import time
import unittest

import requests
import testcase_base
from utils import util

TESTCASE_CALL_DIR = os.path.dirname(os.path.realpath(__file__))
SERVLET_SMS = 'http://localhost:8080/SmsManagerService'

SENDER_PHONE_NUMBER = '2345678910'
TEXT_MESSAGE = 'Hello there'
CMD_SMS_SEND = 'sms send %s %s\n' % (SENDER_PHONE_NUMBER, TEXT_MESSAGE)
CMD_SMS_PDU = ('sms pdu 07911326040000F0040B911346610089F6000020806291'
               '7314080CC8F71D14969741F977FD07\n')
PDU_MESSAGE = 'How are you?'
PDU_PHONE_NUMBER = '+31641600986'
MAX_TRIES = 30


class SmsTest(testcase_base.BaseConsoleTest):
  """This class aims to test sms-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(SmsTest, self).__init__(method_name)
    else:
      super(SmsTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _process_request_sms_service(self, payload):
    """Processes post request to sms service.

    Sends post request to sms service, gets the newest sms message,
    then parses the result to get phone number and text message.

    Args:
        payload: The payload for sending POST request to sms server.

    Returns:
        phone_number: The sender's phone number in the sms message.
        text_message: The text message in the sms.
    """
    r = requests.post(SERVLET_SMS, data=json.dumps(payload))

    if r.raise_for_status():
      error_msg = 'Servlet Error: Post request to %s failed' % SERVLET_SMS
      print error_msg
      return False, error_msg

    r_json = r.json()

    if r_json['isFail']:
      error_msg = ('Servlet Error: Failure occurred in servlet side => %s'
                   % SERVLET_SMS)
      print error_msg
      return False, error_msg

    return r_json['smsAddress'], r_json['smsTextMessage']

  def _poll_sms_and_verify(self, expected_phone_number, expected_text_message):
    """Polls sms message information from emulator and verifies it.

    Args:
      expected_phone_number: Expected phone number to get.
      expected_text_message: Expected sms text message to get.
    """
    got_expected_sms = False
    for i in range(MAX_TRIES):
      got_phone_number, got_sms_message = self._process_request_sms_service(
        {})
      print ('got_phone_number = %s, got_sms_message = %s'
             % (got_phone_number, got_sms_message))
      if (got_phone_number == expected_phone_number
          and got_sms_message == expected_text_message):
        got_expected_sms = True
        break
      else:
        time.sleep(util.TRIAL_WAIT_TIMEOUT_S)

    self.assertTrue(got_expected_sms,
                    'Max tries reached, failed to get expected sms message.')

  def test_send_inbound_sms_text_message(self):
    """Test command for: sms send <phone number> <text message>.

    TT ID: f2c2aa1a-b793-4939-b156-0e7d82c85502
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: sms send <phone number> <text message>, and verify
    Verify:
      An sms is received from <phone number> with the text <text message>.
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip sms test on Win.'
      pass
      return

    print 'Running test: %s' % (inspect.stack()[0][3])

    util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

    is_command_successful, output = util.execute_console_command(
        self.telnet, CMD_SMS_SEND, util.OK)
    self.assert_cmd_successful(
        is_command_successful, 'Failed to properly send sms text message',
        False, '', util.OK, output)
    self._poll_sms_and_verify(SENDER_PHONE_NUMBER, TEXT_MESSAGE)

    util.unstall_apps(TESTCASE_CALL_DIR)

  def test_send_inbound_sms_pdu(self):
    """Test command for: sms send <phone number> <text message>.

    TT ID: f2c2aa1a-b793-4939-b156-0e7d82c85502
    Test steps:
        1. Launch an emulator avd
        2. From command prompt, run: telnet localhost <port>
        3. Copy the auth_token value from ~/.emulator_console_auth_token
        4. Run: auth auth_token
        5. Run: sms pdu <pdu message>
           and verify
    Verify:
        An sms is received from <expected phone number> with
        <expected text> ('How are you?').
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip sms test on Win.'
      pass
      return

    util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

    print 'Running test: %s' % (inspect.stack()[0][3])
    is_command_successful, output = util.execute_console_command(
        self.telnet, CMD_SMS_PDU, util.OK)
    self.assert_cmd_successful(
        is_command_successful, 'Failed to properly send sms pdu',
        False, '', util.OK, output)
    self._poll_sms_and_verify(PDU_PHONE_NUMBER, PDU_MESSAGE)

    util.unstall_apps(TESTCASE_CALL_DIR)


if __name__ == '__main__':
  print '======= sms Test ======='
  unittest.main()
