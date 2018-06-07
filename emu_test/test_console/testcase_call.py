"""Tests for call-related commands."""

import inspect
import json
import os
import time
import unittest

import requests
import testcase_base
from utils import util

TESTCASE_CALL_DIR = os.path.dirname(os.path.realpath(__file__))
SERVLET_TELEPHONY = 'http://localhost:8080/TelephonyManagerService'

CALL_STATE_IDLE = 0
CALL_STATE_RINGING = 1
CALL_STATE_OFFHOOK = 2

CALL_NUMBER = '1234567890'
CMD_GSM_CANCEL = 'gsm cancel %s\n' % CALL_NUMBER
CMD_GSM_CALL = 'gsm call %s\n' % CALL_NUMBER
CMD_GSM_ACCEPT = 'gsm accept %s\n' % CALL_NUMBER


class PhoneCallTest(testcase_base.BaseConsoleTest):
  """This class aims to test call-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(PhoneCallTest, self).__init__(method_name)
    else:
      super(PhoneCallTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _process_request_telephony_service(self, payload):
    r = requests.post(SERVLET_TELEPHONY, data=json.dumps(payload))
    if r.raise_for_status():
      print ('Servlet Error: Post request to %s failed' %
             SERVLET_TELEPHONY)
      return False
    r_json = r.json()
    if r_json['isFail']:
      print ('Servlet Error: Failure occurred in servlet side => %s' %
             SERVLET_TELEPHONY)
      return False
    call_state = int(r_json['description'])
    print 'call_state = %d' % call_state
    return call_state

  def _cancel_inbound_call(self):
    self.telnet.write(CMD_GSM_CANCEL)
    time.sleep(util.CMD_WAIT_TIMEOUT_S)

  def _cancel_inbound_call_verification(self):
    is_cmd_successful, output_cancel_inbound = util.execute_console_command(
        self.telnet, CMD_GSM_CANCEL, util.OK)

    self.assert_cmd_successful(is_cmd_successful,
                               'Failed to properly cancel an inbound call',
                               False, '', util.OK, output_cancel_inbound)
    self.assertTrue(
        self._process_request_telephony_service({}) == CALL_STATE_IDLE,
        'Call state idle not matched')
    time.sleep(util.CMD_WAIT_TIMEOUT_S)

  def _make_inbound_call(self):
    self.assertTrue(
        self._process_request_telephony_service({}) == CALL_STATE_IDLE,
        'Call state idle not matched')

    is_cmd_successful, output_inbound_call = util.execute_console_command(
        self.telnet, CMD_GSM_CALL, util.OK)

    self.assert_cmd_successful(is_cmd_successful,
                               'Failed to properly set up an inbound call',
                               False, '', util.OK, output_inbound_call)

    self.assertTrue(
        self._process_request_telephony_service({}) == CALL_STATE_RINGING,
        'Call state ringing not matched')
    time.sleep(util.CMD_WAIT_TIMEOUT_S)

  def _accept_inbound_call(self):
    is_cmd_successful, output_accept_inbound = util.execute_console_command(
        self.telnet, CMD_GSM_ACCEPT, util.OK)
    self.assert_cmd_successful(is_cmd_successful,
                               'Failed to properly accept an inbound call',
                               False, '', util.OK, output_accept_inbound)
    self.assertTrue(
        self._process_request_telephony_service({}) == CALL_STATE_OFFHOOK,
        'Call state offhook not matched')
    time.sleep(util.CMD_WAIT_TIMEOUT_S)

  def test_inbound_call(self):
    """Test for command: gsm call <phonenumber>.

    TT ID: 5c8892ba-e458-427c-a21d-19758e376749
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: gsm call <phonenumber>, verify 1
      6. Run: gsm cancel <phonenumber>, verify 2
    Verify:
      1. Emulator displays an incoming call from the <phonenumber>
      2. Phone call is terminated.
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip call test on Win.'
      pass
      return

    print 'Running test: %s' % (inspect.stack()[0][3])

    util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

    self._make_inbound_call()
    self._cancel_inbound_call()

    util.unstall_apps(TESTCASE_CALL_DIR)

  def test_accept_call(self):
    """Test for command: gsm accept <phonenumber>.

    TT ID: 5c8892ba-e458-427c-a21d-19758e376749
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: gsm call <phonenumber>, verify 1
      6. Run: gsm accept <phonenumber>, verify 2
      7. Run: gsm cancel <phonenumber>
    Verify:
      1. Emulator displays an incoming call from the <phonenumber>
      2. Emulator displays that the incoming call is accepted
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip call test on Win.'
      pass
      return

    print 'Running test: %s' % (inspect.stack()[0][3])

    util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

    self._make_inbound_call()
    self._accept_inbound_call()
    self._cancel_inbound_call()

    util.unstall_apps(TESTCASE_CALL_DIR)

  def test_terminate_call(self):
    """Test for command: gsm cancel <phonenumber>.

    TT ID: 5c8892ba-e458-427c-a21d-19758e376749
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: gsm call <phonenumber>, verify 1
      6. Run: gsm accept <phonenumber>, verify 2
      7. Run: gsm cancel <phonenumber>, verify 3
    Verify:
      1. Emulator displays an incoming call from the <phonenumber>
      2. Emulator displays that the incoming call is accepted
      3. Phone call is terminated. The emulator displays the phone
         hang-up icon in the notification bar.
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip call test on Win.'
      pass
      return

    print 'Running test: %s' % (inspect.stack()[0][3])

    util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

    self._make_inbound_call()
    self._accept_inbound_call()
    self._cancel_inbound_call_verification()

    util.unstall_apps(TESTCASE_CALL_DIR)


if __name__ == '__main__':
  print '======= Call Test ======='
  unittest.main()
