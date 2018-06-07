"""ADB stress test for device push/pull commands.

usage: adb_push_pull_stress.py [-h] [-d float] [-c int]

optional arguments:
  -h, --help                     Show this help message and exit.
  -d float, --duration float     Duration of time to run stress test (in hrs).
  -c int, --count int            Number of devices/emulators connected.
  -p, --progress                 Print progress.
  --log-dir                      Base directory under which logs will be placed.
"""

from __future__ import print_function
import os
import subprocess
import sys

import util

TEMP_FILE = '__push_file.txt'

# Number of lines in push/pull'd file.
FILE_SIZE = 100


def create_temp_files():
    """Setup for push test.

    Creates all temporary files created used in push test."""
    file = open(TEMP_FILE, 'w')
    for i in range(FILE_SIZE):
        file.write('lorem ipsum\n')
    file.close()


def delete_temp_files():
    """Teardown for push test.

    Deletes all temporary files created for push test.
    """
    try:
        os.remove(TEMP_FILE)
    except OSError:
        pass


def test_push(dut):
    """Verify that pushing a file is successful.

    File size is determined by FILE_SIZE constant.

    Args:
      dut: Device to test against.

    Returns:
      True if successful, else False.
    """
    arg = 'adb -s ' + str(dut) + ' push ' + TEMP_FILE + ' /sdcard/'
    process = subprocess.Popen(arg.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    success = True
    for line in output.split('\n'):
        if line.startswith('adb: error'):
            success = False
            print('\nERROR:\nEPush FAILED for: ' + str(dut))
            print(output)

    return success


def test_pull(dut):
    """Verify that pulling a file is successful.

    File size is determined by FILE_SIZE constant.

    Returns:
      True if successful, else False.
    """
    arg = 'adb -s ' + str(dut) + ' pull /sdcard/' + TEMP_FILE
    process = subprocess.Popen(arg.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    success = True
    for line in output.split('\n'):
        if line.startswith('adb: error'):
            print('\nERROR:\nEPush FAILED for: ' + str(dut))
            print(output)
            success = False

    return success


def test_device(dut):
    """Runs single push/pull against a single device.

    Args:
        dut: device under test
    """
    return test_push(dut) and test_pull(dut)


if __name__ == '__main__':
    args = util.parse_args()
    result = util.launcher(test_device, args.duration, args.count,
                           setup=create_temp_files, cleanup=delete_temp_files,
                           is_print_progress=args.progress,
                           log_dir=os.path.join(args.log_dir, 'adb_push_pull_stress'))

    if result:
        sys.exit(0)
    else:
        sys.exit(1)