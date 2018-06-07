# -*- coding: utf-8 -*-
"""stress test utilities."""

from multiprocessing import pool

import argparse
import os
import subprocess
import sys
import threading
import time
import platform


MAX_CONNECTION_FAILURES = 3


def print_progress(perc, prefix='',
                   suffix='', decimals=1, bar_len=100):
    """Call in a loop to create terminal progress bar.

    Args:
      perc        - Required  : current percentages (Float)
      prefix      - Optional  : prefix string (Str)
      suffix      - Optional  : suffix string (Str)
      decimals    - Optional  : pos number of decimals in % complete (Int)
      barLength   - Optional  : character length of bar (Int)
    """
    format_str = '{0:.' + str(decimals) + 'f}'
    perc_str = format_str.format(perc * 100)
    filled_len = int(round(bar_len * perc))
    bar = '*' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, perc_str, '%', suffix)),
    if perc == 1:
        sys.stdout.write('\n')
    sys.stdout.flush()


class ProgressPrinter(object):
    """Class for printing time-based progress.
    
    Attributes:
        start_time: Time which marks the start of progress.
        stop_time: Time at which the progress is done.
        refresh_delay_s: Time, in seconds, to delay between progress refreshes.
    """
    def __init__(self, start_time, stop_time, refresh_delay_s):
        self.lock = threading.RLock()
        self.start_time = start_time
        self.stop_time = stop_time
        self.refresh_delay_s = refresh_delay_s
        self.is_running = False
        self.timer = None

    def refresh(self):
        duration = self.stop_time - self.start_time
        print_progress(float(time.time() - self.start_time) / duration, prefix='Progress:', suffix='Complete', bar_len=50)

    @property
    def seconds_remaining(self):
        return max(0, self.stop_time - time.time())

    def start(self):
        """Start printing progress."""
        with self.lock:
            if not self.is_running:
                self.is_running = True
                self.tick()

    def tick(self):
        with self.lock:
            if self.is_running and (time.time() < self.stop_time):
                self.refresh()
                self.timer = threading.Timer(self.refresh_delay_s, self.tick)
                self.timer.start()

    def stop(self):
        """Stop printing progress.
        
        Stops printing progress, performing one final refresh."""
        with self.lock:
            if self.is_running:
                self.kill()
                self.refresh()

    def kill(self):
        """Immediately stops printing progress.
        
        Stops printing progress but no final refresh is performed."""
        with self.lock:
            if self.is_running:
                self.is_running = False
                self.timer.cancel()


def get_connected_devices():
    """Returns list of adb device ids that are connected."""
    proc = subprocess.Popen('adb devices'.split(), stdout=subprocess.PIPE)
    output, error = proc.communicate()
    connected = []
    # Collect connected devices.
    # Note that since Windows includes a carriage return, we
    # do it in a seperate loop.
    if platform.system() is not 'Windows':
      for emulator_entry in output.split('\n')[1:]:
        if emulator_entry != '':
          connected.append(emulator_entry.split('\t')[0])
    else:
      for emulator_entry in output.split('\r\n')[1:]:
        if emulator_entry != '':
          connected.append(emulator_entry.split('\t')[0])
    return connected


def test_connected(devices):
    """Verify that the expected number of devices/emulators are still connected.

    Args:
      devices: Number of expected devices.

    Returns:
      A tuple of form (success, connected).
      The success member indicates whether the expected number
      of devices were found.
      The connected member contains a list of device serial numbers
      identifying the connected devices.
    """
    # verify expected emulators/devices are present
    # Note that since Windows includes a carriage return, we do it in a seperate loop.
    connected = get_connected_devices()
    success = True
    if len(connected) != devices:
        print('\n\nERROR:\nExpected number of connections: ' +
              str(devices))
        print('Found: ' + str(len(connected)))

        output, error = shell(['adb', 'devices'])
        print('\n<<<Begin Output of adb devices>>>')
        print(output)
        print('<<<End Output of adb devices>>>')
        print('')
        print('The following devices were detected: %s' % connected)

        success = False

    return success, connected


def noop():
    """Function that does absolutely nothing.
    This is useful as a placeholder / default function
    for function arguments, such as the setup and teardown arguments
    of the launcher function.
    """
    pass


class Atom(object):
    """Class for atomic access and updates to a shared value.
    
    Attributes:
        value: Current state value.
    """
    def __init__(self, initial_value = None):
        self.v = initial_value
        self.lock = threading.Condition()

    @property
    def value(self):
        with self:
            return self.v

    @value.setter
    def value(self, v):
        self.swap(lambda x: v)

    def swap(self, f):
        """Atomically applied f to current value and updates value to the result."""
        with self:
            self.v = f(self.v)

    def __enter__(self):
        return self.lock.__enter__()

    def __exit__(self, *args):
        return self.lock.__exit__(*args)


def launcher(test_fn, duration, devices, setup=noop, cleanup=noop, is_print_progress=False, log_dir='logs'):
    """Higher-order function for launching tests

        Args:
            test_fn: Function that executes a single iteration of a test. This function must take a single argument,
                     which is the device under test, and must return a boolean value indicating the success (True)
                     or failure (False) of the test. Failure may also be indicated by raising an exception.
            duration: Maximum elapsed running time
            devices: Number of expected devices.
            setup: Function that performs any necessary setup steps before the test is run
                   (optional — defaults to noop).
            cleanup: Function that performs any necessary cleanup steps after the test is run
                     (optional — defaults to noop).
            is_print_progress: If True, progress information is printed to stdout after each iteration of the test.
                               If False (the default), progress information is not printed.
                               If any other value (i.e., non-boolean) is provided for this argument,
                               the behaviour of this function is undefined.
            log_dir: base directory under which logs will be placed.

        Returns:
            True if the test ran successfully to completion, otherwise False.
        """

    # ThreadPool for running the tests in parallel.
    # We choose the size to match the number of devices, so that every device can execute in parallel.
    thread_pool = pool.ThreadPool(processes = devices)

    progress_printer = None
    try:
        setup()
        duration_sec = int(duration * 3600)
        start = time.time()
        stop = start + duration_sec
        if is_print_progress:
            progress_printer = ProgressPrinter(start, stop, 60)
            progress_printer.start()

        connection_success, connected = test_connected(devices)
        if not connection_success:
            if devices != 1 or len(connected) == 0:
                return False

        connected_devices = Atom(frozenset(connected))

        def test_device(device):
            connection_failures_remaining = MAX_CONNECTION_FAILURES
            iteration = 0
            success = True
            while time.time() < stop:
                connected = get_connected_devices()
                if device in connected:
                    if not connection_failures_remaining:
                        with connected_devices:
                            if not connected_devices.value:
                                return False
                            else:
                                connected_devices.swap(lambda x: x.union([device]))

                    # Reset remaining connection failures back to max.
                    connection_failures_remaining = MAX_CONNECTION_FAILURES

                    success = test_fn(device) and success
                    log = logcat(device)

                    # Capture logcat.
                    if log:
                        filename = os.path.join(log_dir, device, str(iteration) + '.txt')
                        spit(filename, log)
                else:
                    success = False

                    if connection_failures_remaining:
                        failure_time = time.time() - start
                        filename = os.path.join(log_dir, device, str(iteration) + '.txt')
                        msg = ("Device failed connection test for iteration"
                               + str(iteration)
                               + "(at " + str(failure_time) + "seconds)")
                        spit(filename, msg)

                    connection_failures_remaining = max(0, connection_failures_remaining - 1)

                    if not connection_failures_remaining:
                        with connected_devices:
                             # Remove this device from set of connected devices.
                             connected_devices.swap(lambda x: x.difference([device]))
                             # Too many connection failures, stop the test.
                             return False

                    time.sleep(5)

                iteration += 1

            print('\nInteractions (%s): (%s\n' % (device, iteration))
            return success

        # Run test against every device in parallel.
        results = thread_pool.map(test_device, connected)

        # Verify the results.
        for result in results:
            if not result:
                return False

        # If we get here, the test completed successfully.
        if progress_printer:
            progress_printer.stop()
        print('\nSUCCESS\n')
        return True
    finally:
        if progress_printer:
            progress_printer.kill()
        cleanup()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--duration', metavar='float', type=float, default=1,
        help='Duration of time to run stress test (in hrs)')
    parser.add_argument(
        '-c', '--count', metavar='int', type=int, default=1,
        help='Number of devices/emulators connected')
    parser.add_argument(
        '-p', '--progress', default=False,
        action='store_const', const=True,
        help='Print progress')
    parser.add_argument(
        '--log-dir', type=str, default='logs',
        help='Directory under which log files will be placed (defaults to "logs")')
    return parser.parse_args()


def adb(dut, cmd):
    """Helper function for running adb commands.

    Args:
      dut: Device under tests.
      cmd: List containing adb command to run arguments.

    Returns:
      String containing the comand's output.
    """
    adb_cmd = ['adb', '-s', dut] + cmd
    return subprocess.check_output(adb_cmd)


def logcat(dut):
    """Get logcat of specified device.

    Args:
      dut: Device under test.
      cmd: List containing adb command to run arguments.

    Returns:
      String containing the command's output.
    """
    try:
        cmd = ['shell', 'logcat', '-d', '-v', 'threadtime']
        return adb(dut, cmd)
    except:
        return None


def spit(filename, text):
    """Writes given text to specified file.

    Args:
      filename: Name of file to write to.
      text: The text to write.
    """
    # Ensure the enclosing directory exists.
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write the file.
    out_file = open(filename, 'w+')
    out_file.write(text)
    out_file.close()

def shell(cmd):
    """Executes shell command, returning STDOUT as string and exit code.
    
    Args:
        cmd: List containing command name and arguments.
      
    Returns:
        Tuple (stdout, exit_code) where
          stdout = STDOUT of process
          exit_code = exit code of process
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    return proc.communicate()