# -*- coding: utf-8 -*-
"""stress test utilities."""

import subprocess
import platform


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