"""Test for quit/exit-related commands."""

import inspect
import unittest

import testcase_base
from utils import util

CMD_QUIT = 'quit\n'
CMD_EXIT = 'exit\n'
EMPTY_OUTPUT = ''


class QuitTest(testcase_base.BaseConsoleTest):
  """This class aims to test quit/exit-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(QuitTest, self).__init__(method_name)
    else:
      super(QuitTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def tearDown(self):
    """Override superclass's method.

    In the end of each test case, it already exited from emulator.
    """
    pass

  def _execute_command_and_verify(self, command):
    is_command_successful = False

    self.telnet.write(command)
    util.wait_on_windows()

    output_exit = util.parse_output(self.telnet)
    is_command_successful = (output_exit == EMPTY_OUTPUT)

    self.telnet.close()

    self.assert_cmd_successful(
        is_command_successful, 'Failed to properly quit/exit emulator.',
        False, '', EMPTY_OUTPUT, output_exit)

  def test_quit_command(self):
    """Test command for: quit.

    TT ID: 7a62bc63-b9ff-4895-b216-56f9d2c55b10
    Steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from
         /Users/<username>/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: quit (Verify)
    Verify:
      We have quited from console.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._execute_command_and_verify(CMD_QUIT)

  def test_exit_command(self):
    """Test command for: exit.

    TT ID: 7a62bc63-b9ff-4895-b216-56f9d2c55b10
    Steps:
      1. Launch an emulator avd
      2. From command prompt, run: telnet localhost <port>
      3. Copy the auth_token value from
         /Users/<username>/.emulator_console_auth_token
      4. Run: auth auth_token
      5. Run: exit (Verify)
    Verify:
      We have exited from console.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._execute_command_and_verify(CMD_EXIT)


if __name__ == '__main__':
  print '======= Quit/Exit Test ======='
  unittest.main()
