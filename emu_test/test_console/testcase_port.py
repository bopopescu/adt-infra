"""Tests for port-related commands."""

import inspect
import time
import unittest

import testcase_base
from utils import util

EMULATOR_PORT = '5554'
HOST_PORT = '5556'

CMD_REDIR_LIST = 'redir list\n'
CMD_REDIR_ADD = 'redir add tcp:%s:%s\n' % (HOST_PORT, EMULATOR_PORT)
CMD_REDIR_DEL = 'redir del tcp:%s\n' % HOST_PORT


class PortTest(testcase_base.BaseConsoleTest):
  """This class aims to test redir-related emulator console commands."""

  def __init__(self, method_name=None, avd=None, builder_name=None):
    if method_name:
      super(PortTest, self).__init__(method_name)
    else:
      super(PortTest, self).__init__()
    self.avd = avd
    self.builder_name = builder_name

  def _list_redir_cmd(self):
    is_cmd_succ, output_redir_list = util.execute_console_command(
        self.telnet, CMD_REDIR_LIST, util.PORT_NO_REDIR)
    self.assert_cmd_successful(
        is_cmd_succ, 'Failed to properly list port redirection.',
        False, '', util.PORT_NO_REDIR, output_redir_list)
    return output_redir_list

  def _add_port_redir_cmd(self):
    is_cmd_succ = False

    for i in range(util.NUM_MAX_TRIALS):
      print ('Running %s, trial #%s' %
             (inspect.stack()[0][3], str(i + 1)))

      self.telnet.write(CMD_REDIR_ADD)
      time.sleep(util.CMD_WAIT_TIMEOUT_S)
      output_redir_add = util.parse_output(self.telnet)
      assert output_redir_add == util.OK

      self.telnet.write(CMD_REDIR_LIST)
      time.sleep(util.CMD_WAIT_TIMEOUT_S)
      output_redir_list = util.parse_output(self.telnet)

      is_cmd_succ = (output_redir_list == util.PORT_REDIR_ADD)

      if is_cmd_succ:
        break

      time.sleep(util.TRIAL_WAIT_TIMEOUT)

    self.assert_cmd_successful(
        is_cmd_succ, 'Failed to properly add a new port redirection',
        False, '', util.PORT_REDIR_ADD, output_redir_add)

  def _del_port_redir_cmd(self):
    is_cmd_succ = False

    for i in range(util.NUM_MAX_TRIALS):
      print ('Running : %s, trial #%s' %
             (inspect.stack()[0][3], str(i + 1)))

      self.telnet.write(CMD_REDIR_DEL)
      time.sleep(util.CMD_WAIT_TIMEOUT_S)
      output_redir_del = util.parse_output(self.telnet)
      assert output_redir_del == util.OK

      is_cmd_succ = (self._list_redir_cmd() == util.PORT_NO_REDIR)

      if is_cmd_succ:
        break

      time.sleep(util.TRIAL_WAIT_TIMEOUT_S)

    self.assert_cmd_successful(
        is_cmd_succ, 'Failed to properly delete a port redirection',
        False, '', util.OK, output_redir_del)

  def test_list_port_redir(self):
    """Test for command: redir list.

    TT ID: fa2c6127-83e8-4f36-b5d9-8f87b42ed8eb
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._list_redir_cmd()

  def test_add_new_port_and_delete_port_redir(self):
    """Test for commands: redir.

    redir add <tcp_or_udp>:<5556>:<port_of_emulator>
    redir def <tcp_or_udp>:<5556>
    TT ID: fa2c6127-83e8-4f36-b5d9-8f87b42ed8eb
    b/210442:
      command "redir del" doesn't work on API 23/24 on Windows; but Linux.
    """
    print 'Running test: %s' % (inspect.stack()[0][3])
    self._add_port_redir_cmd()
    self._del_port_redir_cmd()


if __name__ == '__main__':
  print '======= Port Test ======='
  unittest.main()
