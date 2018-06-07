"""
Please note that the below test should work on all screen sizes for Pi images.
Requires environment varaible 'ANDROID_SDK_ROOT' to be set due to path_utils.

This file will attempt to create and then utilize a fingerprint based lock/unlock on the booted emulator image.
"""

import subprocess
import sys
import time
import traceback
import os
import emu_test.utils.path_utils as path_utils
import xml.etree.ElementTree as ET

""" Serial for the running emulator process. """
g_emulator_serial = 'emulator-5554'
if len(sys.argv) == 2:
    g_emulator_serial = sys.argv[1]


def dump_and_pull_screen_xml(filepath):
    """
    Call into ADB to dump out the current window_dump.xml file.  Then copy the dumped file to filepath.
    :param filepath: Local filesystem path to copy the window_dump.xml file to.
    :return: None.
    """
    adb_binary = path_utils.get_adb_binary()
    subprocess.call([adb_binary, '-s', g_emulator_serial, 'shell', 'uiautomator', 'dump'])
    subprocess.call([adb_binary, '-s', g_emulator_serial, 'pull', '/sdcard/window_dump.xml', filepath])


def parse_xml(filepath):
    """
    Parse the passed in XML file and return the root object of that file.
    :param filepath: XML file we wish to parse.
    :return: Root element of XML document.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    return root


def get_middle(bounds):
    """
    Retrieve the middle xy location of the passed in bounds tuple.
    :param bounds: The Bounds of the region to calculate the middle of.  String of [x1,y1,x2,y2].
    :return: [x,y] location representing the middle point of the region.
    """
    aa = bounds.replace('[', ' ')
    bb = aa.replace(']', ' ')
    cc = bb.replace(',', ' ')
    dd = cc.split()
    [x1, y1, x2, y2] = dd
    x = (int(x1) + int(x2)) / 2
    y = (int(y1) + int(y2)) / 2
    return [str(x), str(y)]


def find_location(root, name):
    """
    Given a XML tree and a target node name, find the target node and return its coordinate bounds.
    :param root: XML tree object.
    :param name: Name of the node.text element we wish to search for.
    :return: List of string [x,y] coordinates of the middle of the element.  Or empty list if not found.
    """
    for x in root.iter('node'):
        if name == x.get('text'):
            return get_middle(x.get('bounds'))
    print 'ERROR: Failed to find ' + name + ' node element.'
    return []


def get_middle_location(name):
    """
    Get the location of the middle x,y coordinates of the given named element.
    :param name: Name of the node element we wish to retrieve the
    :return: Return of find_location() function.
    """
    dump_and_pull_screen_xml(name + '.xml')
    root = parse_xml(name + '.xml')
    xy = find_location(root, name)
    return xy


def adb_touch(x, y):
    """
    Perform a emulated touch action at the x,y coordinates passed.
    :param x: X position where we wish to perform emulated touch.
    :param y: Y position where we wish to perform emulated touch.
    :return: None.
    """
    adb_binary = path_utils.get_adb_binary()
    time.sleep(2)
    subprocess.call([adb_binary, 'shell', 'input', 'tap', x, y])
    time.sleep(2)


def adb_touch_button(name):
    """
    Attempts to simulate a button press on the passed in button name for the running emulator.
    :param name: Name of the button element we wish to simulate a press on.
    :return: None.
    """
    tries = 0
    [x, y] = ['0', '0']
    status = False
    while tries < 10:
        coordinates = get_middle_location(name)
        if len(coordinates) == 0:
            print "Failed to find the middle location of %s.  Will try again.", (name)
            time.sleep(2)
            tries = tries + 1
        else:
            [x, y] = coordinates
            status = True
            break
    os.remove(name + ".xml")
    if not status:
        raise Exception("Tried 10 times but still failed to find middle location of " + name)
    adb_touch(x, y)


def adb_input_text(textstr):
    """
    Perform a simulated text input on the running emulator, using the passed textstr as the simulated input.
    :param textstr: String we wish to 'type' into the emulator.
    :return: None.
    """
    adb_binary = path_utils.get_adb_binary()
    time.sleep(2)
    subprocess.call([adb_binary, 'shell', 'input', 'text', textstr])
    time.sleep(2)


def emu_console_finger_touch(finger):
    """
    Simulate a fingerprint touch on the running emulator.  'finger' is the registered fingerprint we are simulating.
    :param finger: Int representing the finger we are simulating a touch for.  eg. '1' means simulate touch of first
        registered finger.
    :return: None.
    """
    adb_binary = path_utils.get_adb_binary()
    time.sleep(2)
    subprocess.call([adb_binary, 'emu', 'finger', 'touch', finger])
    time.sleep(2)


def adb_power_key():
    """
    Simulate touching the power button on the running emulator.  '26' maps to "KEYCODE_POWER" event code.
    :return: None.
    """
    adb_binary = path_utils.get_adb_binary()
    time.sleep(2)
    subprocess.call([adb_binary, 'shell', 'input', 'keyevent', '26'])
    time.sleep(2)


def check_screen_is_unlocked():
    """
    Check if the screen is currently unlocked on the running emulator.
    :return: Boolean.  True if screen is unlocked.  False if screen is locked.
    """
    adb_binary = path_utils.get_adb_binary()
    ret1 = subprocess.call([adb_binary, 'shell', 'dumpsys', 'deviceidle', '|', 'grep', 'mScreenLocked=false'])
    if ret1:
        print 'Emulated screen is not reporting as unlocked.'
        return False
    else:
        print 'Emulated screen is reporting as unlocked.'
        return True


def check_screen_is_locked():
    """
    Check if the screen is currently locked on the running emulator.
    :return: Boolean.  True if the screen is locked.  False if the screen is unlocked.
    """
    adb_binary = path_utils.get_adb_binary()
    ret1 = subprocess.call([adb_binary, 'shell', 'dumpsys', 'deviceidle', '|', 'grep', 'mScreenLocked=true'])
    if ret1:
        print 'Emulated screen is not reporting as locked.'
        return False
    else:
        print 'Emulated screen is reporting as locked.'
        return True


# The below function works on Pi.
def do_fingerprint_test():
    """
    Perform a fingerprint test on the running emulator.  This is done in the following order:
        1.  Enroll a fingerprint.
        2.  Turn off the screen.
        3.  Turn on the screen.
        4.  Check that the screen reports as locked once powered on.
        5.  Simulate a fingerprint touch.
        6.  Check that the screen is reporting as unlocked.
    :return:
    """
    try:
        adb_binary = path_utils.get_adb_binary()
        # Start the fingerprint enroll process.  Then simulate enrollment of finger '1'.
        subprocess.call([adb_binary, 'shell', 'am', 'start', '-n',
                         'com.android.settings/com.android.settings.fingerprint.FingerprintEnrollIntroduction'])
        adb_touch_button('NEXT')
        adb_touch_button('Fingerprint + PIN')
        adb_touch_button('NO')
        adb_input_text('1111')
        adb_touch_button('NEXT')
        adb_input_text('1111')
        adb_touch_button('CONFIRM')
        adb_touch_button('DONE')
        emu_console_finger_touch('1')
        emu_console_finger_touch('1')
        emu_console_finger_touch('1')
        adb_touch_button('DONE')
        # Test that we successfully unlock the device.  We will try 3 times.
        for tries in range(0, 3):
            # Turn off the screen
            adb_power_key()
            # Turn on the screen
            adb_power_key()
            # Check if the device reports as locked
            check_screen_is_locked()
            # Simulate fingerprint touch.
            emu_console_finger_touch('1')
            # Check if the device reports as unlocked.
            ret = check_screen_is_unlocked()
            if ret:
                print 'Successfully tested fingerprint test.'
                return True
        return False
    except Exception as e:
        print 'Exception occurred while attempting fingerprint test'
        print traceback.format_exc()
        return False


if __name__ == '__main__':
    """
    Note that this file requires environment variable 'ANDROID_SDK_HOME' to be set to properly function.
    """
    if not do_fingerprint_test():
        sys.exit(1)

