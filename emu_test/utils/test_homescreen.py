"""
The functions in this file are designed to test Homescreen interaction for googleapis AVD's.
They should have just the launcher as the top activity nothing else.
There are at least two types of potential issues:
    1. There is an activity on top of home activity
    2. There is a pop up on top of home activity
We need to be able to detect and handle both situations.

package="com.google.android.apps.nexuslauncher"
or package='com.android.launcher2"
or package='com.android.launcher3"
"""

import subprocess
import sys
import os
import re
import traceback
import emu_test.utils.path_utils as path_utils
import xml.etree.ElementTree as ET

"""
When we boot the emulator, there should exist only one Stack.  On the top of that stack should be the launcher.
"""

""" EXPECTED_LAUNCHERS are the task names of the launchers we expect to find. """
EXPECTED_LAUNCHERS = ['com.android.launcher', 'nexuslauncher']


def find_num_stack(filename):
    """
    Determines the number of Stacks currently active by parsing the passed file and searching for 'Stack id'.
    :param filename: File we will search for 'Stack id'
    :return: Number of lines in file containing 'Stack id'.
    """
    count = 0
    with open(filename) as f:
        for line in f:
            if 'Stack id' in line:
                count = count + 1
    return count


def get_activity_name(line):
    """
    Return the top activity found from the line.  We find it by searching for regex.
    :param line: Line we will apply regex search on.
    :return: Empty string if no match found, regex match if found.
    """
    p = re.compile(r"topActivity=ComponentInfo{.*\}")
    ms = p.findall(line)
    if ms:
        return ms[0]
    print "Failed to find topActivity=ComponentInfo{.*\} regex."
    return ''


def find_top_activity(filename):
    """
    For the passed filename, search through the file and look for a line with 'topActivity', and call
    get_activity_name() on such a line to find the name of the top activity.
    :param filename: File we will search for the topActivity string in.
    :return: Empty string if filename does not contain matching top activity, name of top activity if found.
    """
    with open(filename) as f:
        for line in f:
            if 'topActivity' in line:
                return get_activity_name(line)
    print 'Failed to find topActivity in %s' % filename
    return ''


def find_home_activity(filename):
    """
    Given the passed in filename, find the topActivity defined within and check if it matches either of the expected
    launchers.
    :param filename: File we will search for the topActivity in.
    :return: Boolean.  True if expected launcher is found, False if expected launcher is not topActivity.
    """
    num_stacks = find_num_stack(filename)
    if num_stacks > 1:
        print 'We have too many stacks.  Expected 1, got %s' % str(num_stacks)
        return False
    top_activity = find_top_activity(filename)
    # If any of the EXPECTED_LAUNCHERS are the top activity, return true.
    if any(launcher in top_activity for launcher in EXPECTED_LAUNCHERS):
        return True
    print "Did not detect expected launcher as top_activity.  Found %s, expected one of %s"\
          % (top_activity, ",".join(EXPECTED_LAUNCHERS))
    return False


def do_activity_test():
    """
    Using adb, dump the current stack list and pull down the dump to the local filesystem.  Then check this dump file
    to see if one of the EXPECTED_LAUNCHERS is labeled as the top_activity.
    :return: Boolean.  Return of function find_home_activity.  True if EXPECTED_LAUNCHER is topActivity. False
        otherwise.
    """
    adb_binary = path_utils.get_adb_binary()
    subprocess.call([adb_binary, 'shell', 'am', 'stack', 'list', '>', '/data/local/tmp/activity.txt'])
    subprocess.call([adb_binary, 'pull', '/data/local/tmp/activity.txt'])
    return find_home_activity('activity.txt')


def find_package(root, name):
    """
    Search all nodes in the passed in XML root for the passed name.
    :param root: XML Root entry.
    :param name: Name of the Node we are searching for.
    :return:  Boolean. True if name is found in XML tree, False otherwise.
    """
    for x in root.iter('node'):
        if name in x.get('package'):
            return True
    return False


def parse_xml(filename):
    """
    Parse the passed in XML. Return the root of the parsed XML.
    :param filename: The XML file we will parse.
    :return: Root Element of the Parsed XML object.
    """
    tree = ET.parse(filename)
    root = tree.getroot()
    return root


def do_popup_test():
    """
    Dump the current UI Window hierarchy and pull down this file. Search this file to see if we can find the target
    EXPECTED_LAUNCHERS entry.
    :return:  Boolean. True if we find one of the expected launchers. False otherwise.
    """
    adb_binary = path_utils.get_adb_binary()
    subprocess.call([adb_binary, 'shell', 'uiautomator', 'dump'])
    subprocess.call([adb_binary, 'pull', '/sdcard/window_dump.xml', 'topscreen.xml'])
    root = parse_xml('topscreen.xml')
    os.remove('topscreen.xml')
    for launcher in EXPECTED_LAUNCHERS:
        active_launcher = find_package(root, launcher)
        if active_launcher:
            return True
    print 'Failed to find one of Launchers %s' % ",".join(EXPECTED_LAUNCHERS)
    return False


def do_homescreen_test():
    """
    Perform a test to see if one of the EXPECTED_LAUNCHERS is active on the emulator task list.
    :return: Boolean. True if we find a EXPECTED_LAUNCHER entry. False if we find no EXPECTED_LAUNCHER.
    """
    try:
        return do_activity_test() and do_popup_test()
    except Exception as e:
        print 'Exception happened during homescreen test. Exception:'
        print traceback.format_exc()
        return False


if __name__ == '__main__':
    """
    Note that environment variable "ANDROID_SDK_ROOT" must be set to resolve location of ADB binary.
    """
    if not do_homescreen_test():
        print 'Homescreen Test suite Failed.'
        sys.exit(1)
    print 'Homescreen Test suite Passed.'
