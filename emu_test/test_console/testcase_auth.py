"""Test for auth-related commands."""

import inspect
import os
import telnetlib
import unittest

import testcase_base
from utils import util

AUTH_OUTPUT = 'Android Console: type \\\'help\\\' for a list of commands\r\nOK'
AUTH_ERROR_OUTPUT = ('KO: authentication token does not match '
                     '~/.emulator_console_auth_token')
AUTH_TOKEN_MISSING_OUTPUT = 'KO: missing authentication token'


class AuthTest(testcase_base.BaseConsoleTest):
  """This class aims to test auth-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(AuthTest, self).__init__(method_name)
    else:
      super(AuthTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def setUp(self):
    """There is nothing to do in setUp()."""
    pass

  def tearDown(self):
    """There is nothing to do in tearDown()."""
    pass

  def _auth_user_for_emulator_console(self, cmd_auth, expected_output):
    is_command_successful, output = util.execute_console_command(
        self.telnet, cmd_auth, expected_output)
    self.assert_cmd_successful(is_command_successful,
                               'Failed to properly authentication.',
                               False, '', expected_output, output)

  def _verify_auth_command_by_enter_help_command(self, expected_output):
    is_command_successful, output = util.execute_console_command(
        self.telnet, util.CMD_HELP, expected_output)

    self.assert_cmd_successful(
        is_command_successful, 'Failed to properly list all command options.',
        False, '', 'Pattern: \n%s' % expected_output, output)

  def _telnet_emulator_with_failure(self):
    self.telnet = telnetlib.Telnet(util.SERVER_NAME, util.CONSOLE_PORT)

    try:
      self.telnet.read_until(
          'Connection closed by foreign host.', util.TIMEOUT_S).strip()
    except EOFError:
      print ('Cannot connect to emulator because auth toke file is not.'
             'accessible.')

  def test_auth_token_file_exists(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. verify 1
      4. Exist emulator console
    Verify:
      1. .emulator_console_auth_token file is created in home folder
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self.telnet = util.telnet_emulator()
    assert os.path.isfile(util.TOKEN_PATH)
    util.exit_emulator_console(self.telnet)

  def test_auth_without_authorization(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Run: help, verify 1
      4. Exist emulator console
    Verify:
      1. Short help information is displayed.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self.telnet = util.telnet_emulator()
    self._verify_auth_command_by_enter_help_command(
        util.REGEX_HELP_DISPLAY_NO_AUTH)
    util.exit_emulator_console(self.telnet)

  def test_auth_user_with_random_auth_token(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Run: help, verify 1
      4. Run: auth <random_auth_token>, verify 1
      5. Exist emulator console
    Verify:
      1. User is not authorized, and warning message is displayed.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self.telnet = util.telnet_emulator()
    self._auth_user_for_emulator_console(util.CMD_RANDOM_AUTH_TOKEN,
                                         AUTH_ERROR_OUTPUT)
    util.exit_emulator_console(self.telnet)

  def test_auth_user_with_empty_auth_token(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Run: help, verify 1
      4. Run: auth <empty_string>, verify 1
      5. Exist emulator console
    Verify:
      1. User is not authorized, and "missing authentication token"
         is displayed.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self.telnet = util.telnet_emulator()
    self._auth_user_for_emulator_console(util.CMD_EMPTY_AUTH_TOKEN,
                                         AUTH_TOKEN_MISSING_OUTPUT)
    util.exit_emulator_console(self.telnet)

  def test_auth_user_with_valid_auth_token(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Run: help, verify 1
      4. Run: auth <valid auth token>, verify 1
      5. Run: help, verify 2
      6. Exist emulator console
    Verify:
      1. User is not authorized
      2. The full help commands information is displayed
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self.telnet = util.telnet_emulator()
    auth_token = util.get_auth_token()
    valid_auth_cmd = '%s %s\n' % (util.AUTH, auth_token)
    self._auth_user_for_emulator_console(valid_auth_cmd, AUTH_OUTPUT)
    self._verify_auth_command_by_enter_help_command(
        util.REGEX_HELP_DISPLAY_AUTH)
    util.exit_emulator_console(self.telnet)

  def test_auth_empty_auth_token_file(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      0. Save valid auth token, and empty the contents of auth token file
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Run: help, verify 1
      4. Reset auth token file
      5. Exist emulator console
    Verify:
      1. Emulator authentication is skipped and emulator console is usable
         (Here, we run help command to check.)
    """
    print 'Running test: %s' % (inspect.stack()[0][3])

    # save auth token value and empty contents of auth token file
    valid_auth_token = util.get_auth_token()

    try:
      f = open(util.TOKEN_PATH, 'w')
      f.close()

      # telnet and verify
      self.telnet = util.telnet_emulator()
      self._verify_auth_command_by_enter_help_command(
          util.REGEX_HELP_DISPLAY_AUTH)

      # reset auth token file
      f = open(util.TOKEN_PATH, 'w')
      f.write(valid_auth_token)
      f.close()

      util.exit_emulator_console(self.telnet)
    except IOError as e:
      print 'IOError on auth token file.'
    finally:
      print ('The failure on resetting auth token file back will affact other '
             'tests running after this test. Hence, reset it again when '
             'failure happens.')
      f = open(util.TOKEN_PATH, 'w')
      f.write(valid_auth_token)
      f.close()

  def test_auth_change_auth_token_file_permissions(self):
    """Test command for: auth <auth_token>.

    TT ID: a808dfe9-b0ff-4b77-9db5-24d8b2aa44ea
    Test steps:
      0. Deny read and write permissions on the auth token file,
         chmod 000 .emulator_console_auth_token
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>, and verify 1
      4. Reset auth token file permissions
         chmod 666 .emulator_console_auth_token
      5. Exist emulator console
    Verify:
      1. Connection to host would be disconnected when auth_token file
         is inaccessible
    """
    # print 'Running test: %s' % (inspect.stack()[0][3])
    # os.chmod(util.TOKEN_PATH, 0000)
    # self._telnet_emulator_with_failure()
    # os.chmod(util.TOKEN_PATH, 0600)

    # TODO: stabilize this test case
    # Currently, the failure of this test will affact other test cases.
    pass


if __name__ == '__main__':
  print '======= auth Test ======='
  unittest.main()