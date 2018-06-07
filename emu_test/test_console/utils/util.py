"""This module contains utility helper functions and constants for console test.

Particularly, parseOutput(telnet) function is extensively used
throughout the entire console test in order to parse the console output until
"OK" message.
"""

import os
from os.path import expanduser
import re
import subprocess
import sys
import telnetlib
import time
from emu_test.utils import path_utils

NEWLINE = '\n'
OK = 'OK'
STATUS = 'status: '
AC = 'AC: '
PRESENT = 'present: '
HEALTH = 'health: '
CAPACITY = 'capacity: '
REGEX_PWR_DISPLAY = 'AC:.*\nstatus:.*\nhealth:.*\npresent:.*\ncapacity:.*\nOK'
COMPARE_CMD = ''
WINDOWS_OS_NAME = 'nt'
if os.name == WINDOWS_OS_NAME:
  COMPARE_CMD = 'FC'
else:
  COMPARE_CMD = 'diff'

SERVER_NAME = 'localhost'
CONSOLE_PORT = 5554

NUM_MAX_TRIALS = 3
TRIAL_WAIT_TIMEOUT_S = 0.5
CMD_WAIT_TIMEOUT_S = 3
SETUP_WAIT_TIMEOUT_S = 5

ADB_TRIAL_WAIT_TIME_S = 2
ADB_NUM_MAX_TRIALS = 5

TIMEOUT_S = 1

HOME = expanduser('~')
CONSOLE_AUTH_TOKEN_FILE_NAME = '.emulator_console_auth_token'
TOKEN_PATH = os.path.join(HOME, CONSOLE_AUTH_TOKEN_FILE_NAME)

UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
EVENT_DIR = os.path.join(UTILS_DIR, 'constants')
EVENTS_CODE_NO_ALIAS = 'no code aliases defined for this type\r\nOK'
EVENTS_CODE_EV_KEY_FILENAME = os.path.join(EVENT_DIR, 'EVENTS_CODE_EV_KEY')
EVENTS_CODE_EV_REL_FILENAME = os.path.join(EVENT_DIR, 'EVENTS_CODE_EV_REL')
EVENTS_CODE_EV_ABS_FILENAME = os.path.join(EVENT_DIR, 'EVENTS_CODE_EV_ABS')
EVENTS_CODE_EV_SW_FILENAME = os.path.join(EVENT_DIR, 'EVENTS_CODE_EV_SW')
EVENTS_EV_TYPES_FILENAME = os.path.join(EVENT_DIR, 'EVENTS_EV_TYPES')
PORT_NO_REDIR = 'no active redirections\r\nOK'
PORT_REDIR_ADD = 'tcp:5556  => 5554 \r\nOK'
CMD_HELP = 'help\n'
REGEX_HELP_DISPLAY_NO_AUTH = (r'.*\n.*help.*\n.*help-verbose.*\n.*ping.*\n'
                              r'.*avd.*\n.*auth.*\n.*quit\|exit.*\n.*\n.*\n.*\nOK')
REGEX_HELP_DISPLAY_AUTH = (r'.*\n.*help.*\n.*help-verbose.*\n.*ping.*\n.*event.*\n'
                           r'.*geo.*\n.*gsm.*\n.*cdma.*\n.*crash.*\n.*crash-on-exit.*\n'
                           r'.*kill.*\n.*network.*\n'
                           r'.*power.*\n.*quit\|exit.*\n.*redir.*\n'
                           r'.*sms.*\n.*avd.*\n.*qemu.*\n.*sensor.*\n.*physics.*\n'
                           r'.*finger.*\n.*debug.*\n.*rotate.*\n.*screenrecord.*\n.*\n.*\n.*\nOK')
CMD_HELP_VERBOSE = 'help-verbose\n'
REGEX_HELP_VERBOSE_DISPLAY_NO_AUTH = (
        r'.*\n.*\n.*help.*\n.*help-verbose.*\n.*ping.*\n'
        r'.*avd.*\n.*auth.*\n.*quit\|exit.*\n.*\n.*\nOK')
REGEX_HELP_VERBOSE_DISPLAY_AUTH = (
        r'.*\n.*\n.*help.*\n.*help-verbose.*\n.*ping.*\n.*event.*\n'
        r'.*geo.*\n.*gsm.*\n.*cdma.*\n.*crash.*\n.*crash-on-exit.*\n'
        r'.*kill.*\n.*network.*\n'
        r'.*power.*\n.*quit\|exit.*\n.*redir.*\n'
        r'.*sms.*\n.*avd.*\n.*qemu.*\n.*sensor.*\n.*physics.*\n'
        r'.*finger.*\n.*debug.*\n.*rotate.*\n.*screenrecord.*\n.*\n.*\nOK')
AUTH = 'auth'
CMD_RANDOM_AUTH_TOKEN = '%s axxB123cc\n' % AUTH
CMD_EMPTY_AUTH_TOKEN = '%s \n' % AUTH
CMD_EXIT = 'exit\n'
SCRIPT_TO_INSTALL_APK = 'install_apk.py'
SCRIPT_TO_RUN_ADB_SHELL = 'run_adb_shell.py'
SCRIPT_TO_UNINSTALL_APP = 'uninstall_app.py'
PYTHON_INTERPRETER = 'python'
CMD_ROTATE = 'rotate\n'
MAIN_APK_PACKAGE = 'com.android.devtools.server'

WIN_BUILDER_NAME = 'Win'


def check_read_until(console_output):
  """Checks whether the console output ends with 'OK' message.

  Args:
    console_output: The console output to be checked.

  Returns:
    A boolean value: It indicates the console output ends with 'OK' message
    or not.
  """
  console_output = console_output.strip()
  index_ok = console_output.rfind(OK)
  return index_ok == len(console_output) - len(OK)


def parse_output(telnet):
  """Parses console output until 'OK' appears.

  Args:
    telnet: The telnet connection to emulator.

  Returns:
    parsed_output: The parsed output until 'OK' message.
  """
  parsed_output = telnet.read_until(OK).strip()
  return parsed_output


def extract_field_from_output(output, keyword):
  """Extract value of specific field from battery command.

  Args:
    output: The output for extracting certain field.
    keyword: The keyword for searching.

  Returns:
    A string value: The field from output searching by given keyword.
  """
  keyword_idx = output.find(keyword)
  return (output[keyword_idx + len(keyword):output.find(NEWLINE, keyword_idx)]
          .strip())


def pattern_match_output(output, regex):
  """Check whether console output matches with a given regex.

  Args:
    output: The console output of a command.
    regex: The regular pattern to use for searching.

  Returns:
    A boolean value: It indicates the pattern is found in the output or not.
  """
  if re.match(regex, output):
    return True
  else:
    return False


def check_battery_status(status):
  """Checking each battery status, used in testcase_battery.py.

  Args:
    status: A battery status to map.

  Returns:
    A string value: The capitalized/mapped battery status.
  """
  if status == 'not-charging':
    return 'Not charging'
  if status == 'failure':
    return 'Unspecified failure'
  if status == 'overheat':
    return 'Overheat'
  return status.capitalize()


def parse_output_for_ev(telnet):
  """Parses console output until 'OK' appears for 'event' command.

  Args:
    telnet: The telnet connection to emulator.

  Returns:
    parsed_output: The parsed console output.
  """
  parsed_output = telnet.read_until('\n%s' % OK).strip()
  return parsed_output


def get_events_code_ev_key():
  """Gets event codes from a static file.

  Returns:
    A string value: The event codes getting from a static file.
  """
  with open(EVENTS_CODE_EV_KEY_FILENAME) as f:
    lines = f.readlines()
  events_code_ev_key = ''
  for line in lines:
    events_code_ev_key += ('\r\n    %s' % line.strip())
  return '%s\r\n%s' % (events_code_ev_key.strip(), OK)


def read_string_from_file(filename):
  """Reads strings written in the file by appending each line.

  Args:
    filename: The file name to read strings from.

  Returns:
    stringRead: A single string value containing each line in the file.
  """
  with open(filename) as f:
    lines = f.readlines()
  string_read = ''
  for line in lines:
    string_read += line
  return string_read


def remove_all_spaces(string):
  """Removes all the trailing spaces and spaces within the string.

  Args:
    string: A string to remove training spaces.

  Returns:
    A string value: A parsed string after removing all trailing spaces.
  """
  return re.sub(r'[\s+]', '', string.strip(' \t\n\r'))


def execute_console_command(telnet, command, expected_output):
  """Executes emulator console command.

  Executes emulator console command through telnet connection,
  compare command output and expected command output.

  Args:
    telnet: The telnet connection to emulator.
    command: The console command to execute.
    expected_output: The expected output for the executed command.

  Returns:
    is_command_successful: It indicates command executed successfully or not.
    output: The command output in the terminal.
  """
  is_command_successful = False

  for i in range(NUM_MAX_TRIALS):
    print 'execute console command: %s, trial #%d' % (command.strip(), i)

    telnet.write(command)
    time.sleep(CMD_WAIT_TIMEOUT_S)

    if command == 'crash\n':
      output = telnet.read_all()
    elif command == CMD_ROTATE: # No 'OK' output showing, only new line.
      print 'command is rotate'
      output = telnet.read_until('\n', 10)
      print 'output = "%s"' % output
    elif command == CMD_EMPTY_AUTH_TOKEN:
      output = telnet.read_until('missing authentication token').strip()
    elif command == CMD_RANDOM_AUTH_TOKEN:
      output = telnet.read_until('emulator_console_auth_token').strip()
    else:
      output = parse_output(telnet)

    is_command_successful = pattern_match_output(output, expected_output)

    if is_command_successful:
      break

    time.sleep(TRIAL_WAIT_TIMEOUT_S)

  return is_command_successful, output


def get_auth_token():
  """Gets auth token value from auth token file.

  Returns:
    auth_token: The value of auth token.
  """
  with open(TOKEN_PATH) as f:
    content = f.readlines()
  auth_token = content[0]
  return auth_token


def telnet_emulator():
  """Only telnet to emulator, initially not need to run auth command."""
  telnet = telnetlib.Telnet(SERVER_NAME, CONSOLE_PORT)
  if not check_read_until(telnet.read_until(OK, TIMEOUT_S)):
    sys.exit(-1)

  return telnet


def wait_on_windows():
  """Waits for few seconds on Windows machine."""
  if os.name == WINDOWS_OS_NAME:
    time.sleep(0.5)


def exit_emulator_console(telnet):
  """Exits from emulator console."""
  telnet.write(CMD_EXIT)
  wait_on_windows()
  telnet.close()


def run_script_run_adb_shell(testcase_call_dir):
  """Run Python script to install apk.

  Run Python script to install Rest Service app and corresponding test on
  Emulator; on emulator, do a port forwarding from tcp:8080 to tcp:8081.

  Args:
    testcase_call_dir: The directory where the test case is called from.
  """
  script_run_adb_shell = ('%s/%s' %
                          (testcase_call_dir, SCRIPT_TO_RUN_ADB_SHELL))
  script_install_apk = '%s/%s' % (testcase_call_dir, SCRIPT_TO_INSTALL_APK)
  adb_binary = path_utils.get_adb_binary()
  subprocess.call([adb_binary, '-s', 'emulator-%s' % str(CONSOLE_PORT),
                   '-e', 'forward', 'tcp:8080', 'tcp:8081'])
  subprocess.call([PYTHON_INTERPRETER, script_install_apk])
  subprocess.Popen([PYTHON_INTERPRETER, script_run_adb_shell])
  time.sleep(SETUP_WAIT_TIMEOUT_S)

def unstall_apps(testcase_call_dir):
  """Run Python script to uninstall apps.

  Args:
    testcase_call_dir: The directory where the test case is called from.
  """
  subprocess.Popen([PYTHON_INTERPRETER,
                    '%s/%s' % (testcase_call_dir, SCRIPT_TO_UNINSTALL_APP)])
  time.sleep(SETUP_WAIT_TIMEOUT_S)
