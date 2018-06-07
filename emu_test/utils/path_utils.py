"""
This file contains functions that return commonly used path locations used throughout emulator testing.

This file requires the environment variable 'ANDROID_SDK_ROOT' to be set, as most paths are relative to this path.
"""

import os


def get_adb_binary():
    """
    Using the current environment variable ANDROID_SDK_ROOT, return the location of the adb command.
    :return: filesystem location of adb binary command.
    """
    adb_binary = os.path.join(os.environ['ANDROID_SDK_ROOT'], 'platform-tools', 'adb')
    return adb_binary


def get_mksdcard_binary():
    """
    Using the current environment variable ANDROID_SDK_ROOT, return the location of the mkdscard command.
    :return: filesystem location of mksdcard binary command.
    """
    mksdcard_binary = os.path.join(os.environ['ANDROID_SDK_ROOT'], 'tools', 'mksdcard')
    return mksdcard_binary


def get_gsutil_path():
    """
    Retrieve the path to the gsutil.py file.  Note that this path is created RELATIVE TO THE emu_test/utils/ directory!
    If you are not executing from a file within this directory, do not use this function.
    :return: Path to the gsutil python file in build/third_party/gsutil/gsutil.py.
    """
    gsutil_path = os.path.join(os.path.dirname(__file__), '..', '..', 'build', 'third_party', 'gsutil', 'gsutil.py')
    return gsutil_path


def get_avdmanager_binary():
    """
    Using the current environment variable ANDROID_SDK_ROOT, return the location of the avdmanager command.
    :return: filesystem location of the avdmanager binary command.
    """
    avdmanager_binary = os.path.join(os.environ['ANDROID_SDK_ROOT'], 'tools', 'bin')
    if os.name == 'nt':
        avdmanager_binary = os.path.join(avdmanager_binary, 'avdmanager.bat')
    else:
        avdmanager_binary = os.path.join(avdmanager_binary, 'avdmanager')
    return avdmanager_binary


def get_sdkmanager_binary():
    """
    Using the current environment variable ANDROID_SDK_ROOT, return the location of the sdkmanager command.
    :return: filesystem location of the sdkmanager binary command.
    """
    sdkmanager_binary = os.path.join(os.environ['ANDROID_SDK_ROOT'], 'tools', 'bin')
    if os.name == 'nt':
        sdkmanager_binary = os.path.join(sdkmanager_binary, 'sdkmanager.bat')
    else:
        sdkmanager_binary = os.path.join(sdkmanager_binary, 'sdkmanager')
    return sdkmanager_binary
