"""Tests for geo-related commands."""

import inspect
import json
import os
import time
import unittest

import requests
import testcase_base
from utils import util

ITERATIONS = 8

TESTCASE_CALL_DIR = os.path.dirname(os.path.realpath(__file__))
SERVLET_GEO = 'http://localhost:8080/GeoManagerService'

CMD_GEO_FIX_PREFIX = 'geo fix'
SF_LONGITUDE = -122
SF_LATITUDE = 38
SF_ALTITUDE = 0
CMD_GEO_SF = ('%s %d %d %d\n' %
              (CMD_GEO_FIX_PREFIX, SF_LONGITUDE, SF_LATITUDE, SF_ALTITUDE))

SF_INVALID_LONGITUDE = 200
SF_INVALID_LATITUDE = 100
CMD_GEO_INVALID = ('%s %d %d %d\n' % (CMD_GEO_FIX_PREFIX, SF_INVALID_LONGITUDE, SF_INVALID_LATITUDE, SF_ALTITUDE))


class GeoTest(testcase_base.BaseConsoleTest):
  """This class aims to test geo-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(GeoTest, self).__init__(method_name)
    else:
      super(GeoTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  # Comment out these class methods for future use when more APIs are added.
  # @classmethod
  # def setUpClass(cls):
  #   util.run_script_run_adb_shell(TESTCASE_CALL_DIR)
  #
  # @classmethod
  # def tearDownClass(cls):
  #   util.unstall_apps(TESTCASE_CALL_DIR)

  def _process_request_geo_service(self, payload):
    """Processes post request to geo service.

    Sends post request to geo service, gets the last known location.

    Args:
        payload: The payload for sending POST request to geo server.

    Returns:
        longitude: The longitude of last know location.
        latitude: The latitude of last know location.
        altitude: The altitude of last know location.
    """
    r = requests.post(SERVLET_GEO, data=json.dumps(payload))

    if r.raise_for_status():
      error_msg = ('Servlet Error: Post request to %s failed' %
                   SERVLET_GEO)
      print error_msg
      return False, error_msg

    r_json = r.json()

    if r_json['isFail']:
      error_msg = ('Servlet Error: Failure occurred in servlet side => %s'
                   % SERVLET_GEO)
      print error_msg
      return False, False, False

    print 'Got longitude: ' + r_json['longitude']
    print 'Got latitude: ' + r_json['latitude']
    print 'Got altitude: ' + r_json['altitude']

    return (int(r_json['longitude']), int(r_json['latitude']),
            int(r_json['altitude']))

  def _poll_geo_and_verify(self,
                           expected_longitude,
                           expected_latitude,
                           expected_altitude):
    """Polls orientation/rotation information from emulator and verifies them.

    Args:
      expected_longitude: Expected longitude to get.
      expected_latitude: Expected latitude to get.
      expected_altitude: Expected altitude to get.
    """
    got_expected = False
    MAX_TRIES = 3
    for i in range(MAX_TRIES):
      got_longitude, got_latitude, got_altitude = \
        self._process_request_geo_service({})
      print ('got_longitude = %s, expected_longitude = %s' %
             (got_longitude, expected_longitude))
      print ('got_latitude = %s, expected_latitude = %s' %
             (got_latitude, expected_latitude))
      print ('got_altitude = %s, expected_altitude = %s' %
             (got_altitude, expected_altitude))
      if (got_longitude == expected_longitude and
            (got_latitude >= expected_latitude - 1 or
              got_latitude <= expected_latitude + 1) and
            got_altitude == expected_altitude):
        got_expected = True
        break
      else:
        time.sleep(util.TRIAL_WAIT_TIMEOUT_S)

    self.assertTrue(got_expected,
                    'Max tries reached, failed to get expected values.')

  def _initially_launch_google_maps_to_have_location_history(self, payload):
    print 'Launch Google Maps initially to make it has location history.'
    requests.post(SERVLET_GEO, data=json.dumps(payload))

  def test_geo(self):
    """Test command for: geo fix xxx

    TT ID: caad94f5-1714-470c-829c-6df616dfa358
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Open Google Maps app and accept the terms and conditions
      6. Enable location service in Google Maps
      7. Tap on My Location
      8. Run: geo fix -122 37 0
    Verify:
      Check Maps location centers on San Francisco.
    """
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip geo test on Win.'
      pass
      return

    print 'Running test: %s' % (inspect.stack()[0][3])

    print 'api = ' + self.avd.api

    if self.avd.api == '23':
      print 'Skip geo test for API 23.'
      pass
      return

    if self.avd.api in ['25', '24', '23']:
      util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

      self._initially_launch_google_maps_to_have_location_history({'api': self.avd.api})

      is_command_successful, output = util.execute_console_command(
        self.telnet, CMD_GEO_SF, '')
      self.assert_cmd_successful(
        is_command_successful, 'Failed to properly set geo info.',
        False, '', '', output)
      self._process_request_geo_service({})
      self._poll_geo_and_verify(SF_LONGITUDE, SF_LATITUDE, SF_ALTITUDE)

      util.unstall_apps(TESTCASE_CALL_DIR)
    else:
      # TODO: Add support for APIs below 23.
      print 'API is below 23, skip geo test for now.'
      pass

  @unittest.skip("Skip it because it failed, and also can be repo locally on Linux with API 25/26.")
  def test_geo_stress(self):
    """Stress geo location by attempting to send invalid coordinates."""
    if util.WIN_BUILDER_NAME in self.builder_name:
      print 'Skip geo test on Win.'
      pass
      return

    print 'Running test: %s' % (inspect.stack()[0][2])

    if self.avd.api in ['24', '25']:
      print 'Running test: %s' % (inspect.stack()[0][2])

      util.run_script_run_adb_shell(TESTCASE_CALL_DIR)

      self._initially_launch_google_maps_to_have_location_history({'api': self.avd.api})
      is_command_successful, output = util.execute_console_command(self.telnet, CMD_GEO_SF, '')
      self.assert_cmd_successful(is_command_successful, 'Failed to properly set geo info.',
                                 False, '', '', output)
      self._process_request_geo_service({})
      self._poll_geo_and_verify(SF_LONGITUDE, SF_LATITUDE, SF_ALTITUDE)

      for i in range(ITERATIONS):
        # Use telnet.write directly instead of execute_console_command since we expect this command to fail.
        # Will produce 'KO' rather than 'OK'. (i.e. execute_console_command hangs waiting for 'OK').
        self.telnet.write(CMD_GEO_INVALID)
        self.telnet.read_until('KO:')
        self.telnet.read_until('\n')
        self._process_request_geo_service({})
        self._poll_geo_and_verify(SF_LONGITUDE, SF_LATITUDE, SF_ALTITUDE)

      util.unstall_apps(TESTCASE_CALL_DIR)
    else:
      # TODO: Add support for APIs below 24.
      print 'Skip geo stress test for APIs below 24.'
      pass


if __name__ == '__main__':
  print '======= geo Test ======='
  unittest.main()
