"""Tests for battery-related commands."""

import inspect
import time
import unittest

import testcase_base
from utils import util

CMD_POWER_DISPLAY = 'power display\n'
CMD_POWER_AC_PREFIX = 'power ac'
CMD_POWER_STATUS_PREFIX = 'power status'
CMD_POWER_HEALTH_PREFIX = 'power health'
CMD_POWER_PRESENT_PREFIX = 'power present'
CMD_POWER_CAPACITY_PREFIX = 'power capacity'

STATUS_ASSERT_MSG_PREFIX = 'Failed to set power status to'
PRESENCE_ASSERT_MSG_PREFIX = 'Failed to set power presence to'
HEATH_ASSERT_MSG_PREFIX = 'Failed to set power health to'
REMAINING_75 = '75'
CAPACITY_ASSERT_MSG_PREFIX = ('Failed to set remaining battery to %s'
                              % REMAINING_75)
CHARGING_STATUS = 'charging'
GOOD_STATUS = 'good'


class BatteryTest(testcase_base.BaseConsoleTest):
  """Tests for battery-related commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(BatteryTest, self).__init__(method_name)
    else:
      super(BatteryTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _reset_status_back_to_charging(self):
    self._set_battery_status(CHARGING_STATUS)

  def _reset_health_back_to_good(self):
    self._set_health_state(GOOD_STATUS)

  def _reset_capacity_back_to_100(self):
    REMAINING_100 = '100'
    assert_msg = '%s %s' % (HEATH_ASSERT_MSG_PREFIX, REMAINING_100)
    self._set_power_test(CMD_POWER_CAPACITY_PREFIX, REMAINING_100,
                         assert_msg, util.CAPACITY)

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
                               'Pattern: \n%s' % expected_output, output)

  def _get_power_display(self):
    """Gets the console output for 'power display' command.

    Returns:
        output_pwr_display: The console output for 'power display' command.
    """
    self.telnet.write(CMD_POWER_DISPLAY)
    time.sleep(util.CMD_WAIT_TIMEOUT_S)
    output_pwr_display = util.parse_output(self.telnet)
    return output_pwr_display

  def _set_power_test(self, command_prefix, status, assert_msg, keyword):
    """Sets the test scenario for power.

    Args:
        command_prefix: The sub command prefix for power.
        status: The status to be set.
        assert_msg: The assertion message.
        keyword: Keyword used for searching in the console output.
    """
    is_command_successful, output = util.execute_console_command(
        self.telnet, '%s %s\n' % (command_prefix, status), util.OK)
    self.assert_cmd_successful(is_command_successful, assert_msg, False, '',
                               'Pattern: \n%s' % util.OK, output)

    is_cmd_successful = False
    for i in range(util.NUM_MAX_TRIALS):
      print ('Running: %s, retrieve status %s, trial # %s'
             % (inspect.stack()[0][3], status, str(i + 1)))
      output_pwr_display = self._get_power_display()
      output_extracted = util.extract_field_from_output(
          output_pwr_display, keyword)

      if CMD_POWER_AC_PREFIX == command_prefix:
        is_cmd_successful = (output_extracted == ('%sline' % status))
      elif (command_prefix in
            (CMD_POWER_STATUS_PREFIX, CMD_POWER_HEALTH_PREFIX)):
        correct_output = util.check_battery_status(status)
        is_cmd_successful = (output_extracted == correct_output)
      elif CMD_POWER_PRESENT_PREFIX == command_prefix:
        is_cmd_successful = output_extracted
      elif CMD_POWER_CAPACITY_PREFIX == command_prefix:
        is_cmd_successful = (output_extracted == status)
      else:
        print 'Un-handled command prefix: %s' % command_prefix

      if is_cmd_successful:
        break
      time.sleep(util.TRIAL_WAIT_TIMEOUT_S)
    print ('Test result: %s %s => %s'
           % (inspect.stack()[0][3], status, str(is_cmd_successful)))
    self.assert_cmd_successful(is_cmd_successful,
                               'Failed to retrieve power status as %s' % status,
                               True, status, '%s' % status, output_extracted)

  def _set_battery_status(self, status):
    assert_msg = '%s %s' % (STATUS_ASSERT_MSG_PREFIX, status)
    self._set_power_test(CMD_POWER_STATUS_PREFIX, status,
                         assert_msg, util.STATUS)

  def _set_presence_state(self, status):
    assert_msg = '%s %s' % (PRESENCE_ASSERT_MSG_PREFIX, status)
    self._set_power_test(CMD_POWER_PRESENT_PREFIX, status,
                         assert_msg, util.PRESENT)

  def _set_health_state(self, status):
    assert_msg = '%s %s' % (HEATH_ASSERT_MSG_PREFIX, status)
    self._set_power_test(CMD_POWER_HEALTH_PREFIX, status,
                         assert_msg, util.HEALTH)

  def test_power_display(self):
    """Test for command: power ac <on_or_off>.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power display, and verify 1
    Verify:
      1. Power details are displayed
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    assert_msg = 'Failed to properly display power details.'
    self._execute_command_and_verify(CMD_POWER_DISPLAY, util.REGEX_PWR_DISPLAY,
                                     assert_msg)

  def test_set_ac_charge_state(self):
    """Test for command: power ac <on_or_off>.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power ac on
      6. Run: power display, and verify 1
      7. Run: power ac off
      8. Run: power display, and verify 2
    Verify:
      1. Emulator displays AC as online
      2. Emulator displays AC as offline
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    assert_msg = 'Failed to properly display power details.'
    self._set_power_test(CMD_POWER_AC_PREFIX, 'off', assert_msg, util.AC)
    self._set_power_test(CMD_POWER_AC_PREFIX, 'on', assert_msg, util.AC)

  def test_set_battery_status_to_unknown(self):
    """Test for command: power status unknown.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power status unknown, and verify 1
    Verify:
      1. Success to set power status to unknown
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_battery_status('unknown')
    self._reset_status_back_to_charging()

  def test_set_battery_status_to_charging(self):
    """Test for command: power status charging.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power status charging, and verify 1
    Verify:
      1. Success to set power status to charging
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_battery_status(CHARGING_STATUS)

  def test_set_battery_status_to_discharging(self):
    """Test for command: power status discharging.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power status discharging, and verify 1
    Verify:
      1. Success to set power status to discharging
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_battery_status('discharging')
    self._reset_status_back_to_charging()

  def test_set_battery_status_to_not_charging(self):
    """Test for command: power status not-charging.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power status not-charging, and verify 1
    Verify:
      1. Success to set power status to not-charging
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_battery_status('not-charging')
    self._reset_status_back_to_charging()

  def test_set_battery_status_to_full(self):
    """Test for command: power status full.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power status full, and verify 1
    Verify:
      1. Success to set power status to full
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_battery_status('full')
    self._reset_status_back_to_charging()

  def test_set_presence_state(self):
    """Test for command: power present <true_or_false>.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power present true, and verify 1
      6. Run: power present false, and verify 2
    Verify:
      1. Success to set power presence to True
      2. Success to set power presence to False
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_presence_state('false')
    self._set_presence_state('true')

  def test_set_battery_health_to_unknown(self):
    """Test for command: power health unknown.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power health unknown, and verify 1
    Verify:
      1. Success to set power health to unknown
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_health_state('unknown')
    self._reset_health_back_to_good()

  def test_set_battery_health_to_good(self):
    """Test for command: power health good.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power health good, and verify 1
    Verify:
      1. Success to set power health to good
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_health_state('good')

  def test_set_battery_health_to_overheat(self):
    """Test for command: power health overheat.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power health overheat, and verify 1
    Verify:
      1. Success to set power health to overheat
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_health_state('overheat')
    self._reset_health_back_to_good()

  def test_set_battery_health_to_dead(self):
    """Test for command: power health dead.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power health dead, and verify 1
    Verify:
      1. Success to set power health to dead
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_health_state('dead')
    self._reset_health_back_to_good()

  def test_set_battery_health_to_overvoltage(self):
    """Test for command: power health overvoltage.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power health overvoltage, and verify 1
    Verify:
      1. Success to set power health to overvoltage
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_health_state('overvoltage')
    self._reset_health_back_to_good()

  def test_set_battery_health_to_failure(self):
    """Test for command: power health failure.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power health failure, and verify 1
    Verify:
      1. Success to set power health to failure
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._set_health_state('failure')
    self._reset_health_back_to_good()

  def test_set_remaining_battery_capacity(self):
    """Test for command: power capacity 75.

    TT ID: af55c29a-062a-41d9-a549-b8545840abad
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from ~/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: power capacity 75, and verify 1
    Verify:
      1. Success to set power capacity to 75
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    assert_msg = '%s %s' % (HEATH_ASSERT_MSG_PREFIX, REMAINING_75)
    self._set_power_test(CMD_POWER_CAPACITY_PREFIX, REMAINING_75,
                         assert_msg, util.CAPACITY)
    self._reset_capacity_back_to_100()


if __name__ == '__main__':
  print '======= Battery Test ======='
  unittest.main()
