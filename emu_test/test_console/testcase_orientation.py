"""Tests for rotate-related commands."""

import inspect
import json
import os
import time
import unittest

import requests
import testcase_base
from utils import util

TESTCASE_CALL_DIR = os.path.dirname(os.path.realpath(__file__))
SERVLET_ORIENTATION = 'http://localhost:8080/OrientationManagerService'

MAX_TRIES = 3

ROTATION_0 = 0
ROTATION_270 = 3
ROTATION_180 = 2
ROTATION_90 = 1

ORIENTATION_PORTRAIT = 1
ORIENTATION_LANDSCAPE = 2


class OrientationTest(testcase_base.BaseConsoleTest):
  """This class aims to test rotate-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(OrientationTest, self).__init__(method_name)
    else:
      super(OrientationTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _process_request_orientation_service(self, payload):
    """Processes post request to orientation service.

    Sends post request to sms service, gets the orientation and rotation.

    Args:
        payload: The payload for sending POST request to sms server.

    Returns:
        orientation: The orientation of the screen.
        rotation: The rotation of the screen.
    """
    r = requests.post(SERVLET_ORIENTATION, data=json.dumps(payload))

    if r.raise_for_status():
      error_msg = ('Servlet Error: Post request to %s failed' %
                   SERVLET_ORIENTATION)
      print error_msg
      return False, error_msg

    r_json = r.json()

    if r_json['isFail']:
      error_msg = ('Servlet Error: Failure occurred in servlet side => %s'
                   % SERVLET_ORIENTATION)
      print error_msg
      return False, error_msg

    return int(r_json['screenOrientation']), int(r_json['screenRotation'])

  def _poll_orientation_rotation_and_verify(self, expected_orientation,
                                            expected_rotation):
    """Polls orientation/rotation information from emulator and verifies them.

    Args:
      expected_orientation: Expected orientation to get.
      expected_rotation: Expected rotation to get.
    """
    got_expected = False
    for i in range(MAX_TRIES):
      got_orientation, got_rotation = self._process_request_orientation_service(
        {})
      print ('got_orientation = %s, expected_orientation = %s' %
             (got_orientation, expected_orientation))
      print ('got_rotation = %s, expected_rotation = %s' %
             (got_rotation, expected_rotation))
      if (got_orientation == expected_orientation and
            got_rotation == expected_rotation):
        got_expected = True
        break
      else:
        # Emulator needs some time to update the rotation of it's display.
        time.sleep(2)

    self.assertTrue(got_expected,
                    'Max tries reached, failed to get expected values.')

  def _execute_rotate_command_and_verify(self, expected_orientation,
                                         expected_rotation):
    print '\n-------------------------'
    is_command_successful, output = util.execute_console_command(
      self.telnet, util.CMD_ROTATE, '')
    self.assert_cmd_successful(
      is_command_successful, 'Failed to properly get orientation/rotation.',
      False, '', '', output)
    self._poll_orientation_rotation_and_verify(expected_orientation,
                                               expected_rotation)

  def test_orientation(self):
    """Test command for: rotate

    TT ID: a802e7d8-75e6-44fd-ac9c-5af3f8d5d3a2
    Test steps:
      1. Launch an emulator avd
      2. Open any app, say Calculator, or maps
      3. From command prompt, run: telnet localhost <port>
      4. Copy the auth_token value from ~/.emulator_console_auth_token
      5. Run: auth auth_token
      6. Run: rotate, and verify
    Verify:
      Check to orientation and rotation of the launched app.
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip orientation test on Win.'
      pass
      return

    util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

    print 'Running test: %s' % (inspect.stack()[0][3])
    self._poll_orientation_rotation_and_verify(ORIENTATION_PORTRAIT, ROTATION_0)
    self._execute_rotate_command_and_verify(ORIENTATION_LANDSCAPE, ROTATION_270)

    util.unstall_apps(TESTCASE_CALL_DIR)


if __name__ == '__main__':
  print '======= rotate Test ======='
  unittest.main()
