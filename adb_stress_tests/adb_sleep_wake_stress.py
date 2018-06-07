"""ADB stress test for sleep/wake.

usage: adb_sleep_wake_stress.py [-h] [-d float] [-c int]

optional arguments:
  -h, --help                     Show this help message and exit.
  -d float, --duration float     Duration of time to run stress test (in hrs).
  -c int, --count int            Number of devices/emulators connected.
  -p, --progress                 Print progress.
  --log-dir                      Base directory under which logs will be placed.
"""

import os
import subprocess
import sys

import util


def test_sleep(dut):
    """Verify that putting the device to sleep is successful.

    Args:
      dut: Serial number of device to connect to.

    Returns:
      True if the device was successfully put to sleep, else False
    """
    # Simulate power button press.
    # It would be good if we verified the device was currently awake.
    # Otherwise, this will actually wake up the device.
    arg = 'adb -s ' + str(dut) + ' shell input keyevent POWER'
    process = subprocess.Popen(arg.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    success = True
    for line in output.split('\n'):
        if line.startswith('adb: error'):
            success = False
            print('\nERROR:\nFAILED to put device to sleep: ' + str(dut))
            print(output)

    return success


def test_wake(dut):
    """Verify that the device can be woken up.

    Args:
      dut: Serial number of device under test.

    Returns:
      True if the device was successfully woken up, else False.
    """
    arg = 'adb -s ' + str(dut) + ' shell input keyevent POWER'
    process = subprocess.Popen(arg.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    success = True
    for line in output.split('\n'):
        if line.startswith('adb: error'):
            print('\nERROR:\nFAILED to wake device: ' + str(dut))
            print(output)
            success = False

    return success


def test_device(dut):
    return test_sleep(dut) and test_wake(dut)


if __name__ == '__main__':
    args = util.parse_args()
    result = util.launcher(test_device, args.duration, args.count, is_print_progress=args.progress,
                           log_dir=os.path.join(args.log_dir, 'adb_sleep_wake_stress'))

    if result:
        sys.exit(0)
    else:
        sys.exit(1)