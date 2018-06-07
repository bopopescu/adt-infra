"""Tests for event-related commands."""

import inspect
import time
import unittest

import testcase_base
from utils import util

EVENT = 'event'
CMD_EVENT_TYPES = '%s types\n' % EVENT
CMD_EVENT_CODES_PRE = '%s codes' % EVENT
CMD_EVENT_CODES_EV_SYN = '%s EV_SYN\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_MSC = '%s EV_MSC\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_SW = '%s EV_SW\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_LED = '%s EV_LED\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_SND = '%s EV_SND\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_REP = '%s EV_REP\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_FF = '%s EV_FF\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_PWR = '%s EV_PWR\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_FF_STATUS = '%s EV_FF_STATUS\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_MAX = '%s EV_MAX\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_KEY = '%s EV_KEY\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_REL = '%s EV_REL\n' % CMD_EVENT_CODES_PRE
CMD_EVENT_CODES_EV_ABS = '%s EV_ABS\n' % CMD_EVENT_CODES_PRE


class EventTest(testcase_base.BaseConsoleTest):
  """This class aims to test event-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(EventTest, self).__init__(method_name)
    else:
      super(EventTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _verify_events_no_alias(self, command):
    is_cmd_successful, output_event_list_all = util.execute_console_command(
        self.telnet, command, util.EVENTS_CODE_NO_ALIAS)

    self.assert_cmd_successful(
        is_cmd_successful,
        'output mismatch: fail to run %s properly' % command,
        False, '', util.EVENTS_CODE_NO_ALIAS, output_event_list_all)

  def _verify_all_events_no_allias(self):
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_SYN)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_MSC)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_LED)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_SND)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_REP)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_FF)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_PWR)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_FF_STATUS)
    self._verify_events_no_alias(CMD_EVENT_CODES_EV_MAX)

  def _verify_event_codes(self, command, filename):
    is_cmd_successful = False
    for i in range(util.NUM_MAX_TRIALS):
      print ('Running: %s verified against %s, trial #%s' %
             (inspect.stack()[0][3], filename.strip(), str(i + 1)))
      self.telnet.write(command)
      time.sleep(util.CMD_WAIT_TIMEOUT_S)
      output_event_list_all = util.remove_all_spaces(
          util.parse_output_for_ev(self.telnet))
      correct_output = util.remove_all_spaces(
          util.read_string_from_file(filename))
      is_cmd_successful = (output_event_list_all == correct_output)
      if is_cmd_successful:
        break
      time.sleep(util.TRIAL_WAIT_TIMEOUT_S)
    self.assert_cmd_successful(
        is_cmd_successful, 'output mismatch: fail to run %s properly' % command,
        False, '', correct_output, output_event_list_all)

  def _verify_all_event_codes(self):
    self._verify_event_codes(CMD_EVENT_CODES_EV_KEY,
                             util.EVENTS_CODE_EV_KEY_FILENAME)
    self._verify_event_codes(CMD_EVENT_CODES_EV_REL,
                             util.EVENTS_CODE_EV_REL_FILENAME)
    self._verify_event_codes(CMD_EVENT_CODES_EV_ABS,
                             util.EVENTS_CODE_EV_ABS_FILENAME)
    self._verify_event_codes(CMD_EVENT_CODES_EV_SW,
                             util.EVENTS_CODE_EV_SW_FILENAME)

  def test_list_event_aliases(self):
    """Test for command: event types.

    TT ID: b15436dd-dd0a-4943-aee7-41301cbe18e3
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: event types
      6. verify 1
    Verify:
      1. Available event types are listed
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    is_cmd_successful = False
    for i in range(util.NUM_MAX_TRIALS):
      print ('Running: %s, trial #%s' %
             (inspect.stack()[0][3], str(i + 1)))
      self.telnet.write(CMD_EVENT_TYPES)
      time.sleep(util.CMD_WAIT_TIMEOUT_S)
      output_event_aliases = util.remove_all_spaces(
          util.parse_output_for_ev(self.telnet))
      correct_output = util.remove_all_spaces(
          util.read_string_from_file(util.EVENTS_EV_TYPES_FILENAME))
      is_cmd_successful = (output_event_aliases == correct_output)

      if is_cmd_successful:
        break
      time.sleep(util.TRIAL_WAIT_TIMEOUT_S)

    self.assert_cmd_successful(
        is_cmd_successful, 'Listing all aliases of events failed',
        False, '', correct_output, output_event_aliases)

  def test_list_all_code_aliases(self):
    """Test for command: event codes <type>" (for example: event codes EV_REL).

    TT ID: b15436dd-dd0a-4943-aee7-41301cbe18e3
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run several "event codes <type>" commands
      6. verify 1
    Verify:
      1. Available event code alias for the selected type are listed
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._verify_all_event_codes()
    self._verify_all_events_no_allias()

  def test_simulate_key_presses(self):
    """Test for command: event text <message>.

    TT ID: b15436dd-dd0a-4943-aee7-41301cbe18e3
    """
    # b/204884
    print 'Running test: %s' % (inspect.stack()[0][3])
    pass


if __name__ == '__main__':
  print '======= Event Test ======='
  unittest.main()
