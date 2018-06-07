"""ADB device restart stress test.

Test covers bug https://issuetracker.google.com/issues/70244520

usage: adb_restart_stress.py [-h] [-d float] [-c int]

optional arguments:
  -h, --help                     Show this help message and exit.
  -d float, --duration float     Duration of time to run stress test (in hrs).
  -c int, --count int            Number of devices/emulators connected.
  -p, --progress                 Print progress.
  --log-dir                      Base directory under which logs will be placed.
"""

import subprocess
import time
import sys

import util


def test_restart():
    """Verify that restarting ADB is successful.
    
    Returns:
      True if successful, else False.
    """
    process = subprocess.Popen(['adb', 'kill-server'], stdout=subprocess.PIPE)
    output, error = process.communicate()
    success = True
    if process.returncode != 0:
        success = False

    for line in output.split('\n'):
        if line.startswith('adb: error'):
            success = False
            break

    if not success:
        print('\nERROR:\nFAILED to kill ADB:')
        print(output)
        return False

    process = subprocess.Popen(['adb', 'start-server'], stdout=subprocess.PIPE)
    output, error = process.communicate()

    success = True
    if process.returncode != 0:
        success = False

    for line in output.split('\n'):
        if line.startswith('adb: error') or ("ADB server didn't ACK") in line:
            success = False
            break

    if not success:
        print('\nERROR:\nFAILED to start ADB:')
        print(output)
        return False

    return True


def launcher(duration, device_count):
    """Launch test
    
    Args:
      duration: Amount of time (in hours) for which to run the test.
      device_count: Number of devices expected to be connected.
      
    Returns:
      True if all iterations succeed, else False.
    """
    start_time = time.time()
    duration_sec = int(duration * 3600)
    end_time = start_time + duration_sec
    iteration = 0
    connection_success, connected = util.test_connected(device_count)
    if not connection_success:
        if device_count != 1 or len(connected) == 0:
            return False

    while time.time() < end_time:
        print('Running iteration: %s' % iteration)
        if not test_restart():
            return False
        if not util.test_connected(device_count):
            return False
        iteration += 1
    return True


if __name__ == '__main__':
    import platform
    if platform.system() == 'Windows':
        print('Skipping adb_restart_stress on Windows')
        sys.exit(0)
    args = util.parse_args()
    result = launcher(args.duration, args.count)
    if result:
        sys.exit(0)
    else:
        sys.exit(1)