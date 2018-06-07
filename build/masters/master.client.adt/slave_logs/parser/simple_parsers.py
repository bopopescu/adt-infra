# Copyright 2016 The Android Open Source Project
#
# This software is licensed under the terms of the GNU General Public
# License version 2, as published by the Free Software Foundation, and
# may be copied, distributed, and modified under those terms.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""Some standard parsing functions used to parse common log files"""

import datetime
import json
import re


def re_match_one_in_file(regexes, ifile):
    """Searches for the first match of given regular expressions in the file.

    TODO(pprabhu): Update docstring.
    Args:
        regexes: [(regex, (match_names))] A map from arbitrary keys to compiled
                regex objects to match against.
        ifile: Input file opened in read mode.
    Returns:
        {regex_name: match_object}: A map from input regex_names to a tuple of
        matched strings. Only explicitly captured groups are returned as a
        tuple. (See re.groups).
        Only matching regexes are included in the map.
    """
    matches = {}
    for line in ifile:
        for regex, match_names in regexes:
            match = regex.match(line)
            if match is None:
                continue
            for key, value in zip(match_names, match.groups()):
                if value is not None:
                    matches[key] = value
    return matches

# Use the following with |re_match_one_in_file| for common parsing operations.
# Typical usage:
#
# with open('some_path.log') as my_file:
#     matches = re_match_one_in_file(AVD_REGEXES, my_file):
#     # ___ OR ___
#     my_regexes = list(AVD_REGEXES)
#     my_regexes += list(BUILDBOT_RUN_REGEXES)
#     with open('some_path.log') as my_file:
#         matches = re_match_one_in_file(my_regexes, my_file):
# if AVD_API in matches:
#   # Use matches[AVD_API], guaranteed to not be None.

AVD_API = 'API'
# TAG is custom tag that we use to separate out different kinds of images.
# Possible values: 'default', 'google_apis', 'android-tv', 'android-wear'
AVD_TAG = 'TAG'
AVD_ABI = 'ABI'
AVD_DEVICE = 'DEVICE'
AVD_RAM = 'RAM'
AVD_GPU = 'GPU'
# This takes the values: 'qemu1', 'qemu2'
AVD_QEMU_ENGINE = 'QEMU_ENGINE'
AVD_REGEXES = (
        (re.compile('.*(default|google_apis|android-tv|android-wear)-'
                    '(.*)-(.*)-(\d+)-gpu_(.*)-api(\d+)'),
         (AVD_TAG, AVD_ABI, AVD_DEVICE, AVD_RAM, AVD_GPU, AVD_API)),
        (re.compile(".*INFO - Running - .*(qemu(?:1|2))"),
         (AVD_QEMU_ENGINE,)),
)

# Buildbot run related information.
BUILDBOT_START_TIME = 'BUILDBOT_START_TIME'
BUILDBOT_END_TIME = 'BUILDBOT_END_TIME'
BUILDBOT_REGEXES = (
        (re.compile("(.*) - INFO - Running - test_.*"),
         (BUILDBOT_START_TIME,)),
        (re.compile("(.*) - INFO - copy CTS log from .*"),
         (BUILDBOT_END_TIME,)),
)

BOOT_TIME = 'BOOT_TIME'
# This doesn't actually contain a value. The existence of this key in the result
# implies boot failure.
BOOT_FAIL = 'BOOT_FAIL'
# This captures the amount of time after which we timed out.
BOOT_TIMEOUT = 'BOOT_TIMEOUT'
BOOT_REGEXES = (
        (re.compile(".*AVD .*, boot time: (\d*.?\d*), expected time: \d+"),
         (BOOT_TIME,)),
        (re.compile('^FAIL: test_boot_.*_qemu\d+ '
                    '(\(test_boot.test_boot.BootTestCase\))$'),
         (BOOT_FAIL,)),
        (re.compile(".*ERROR - AVD .* didn't boot up within (\d+) seconds"),
         (BOOT_TIMEOUT,)),
)

ADB_PUSH_SPEED = 'ADB_PUSH_SPEED'
ADB_PULL_SPEED = 'ADB_PULL_SPEED'
ADB_SPEED_REGEXES = (
        (re.compile('.*- INFO - AVD .*, adb push: (\d+) KB/s, adb pull: '
                    '(\d+) KB/s'),
         (ADB_PUSH_SPEED, ADB_PULL_SPEED)),
)

CTS_LOG_DIR = 'CTS_LOG_DIR'
CTS_NUM_TESTS_PASSED = 'CTS_NUM_TESTS_PASSED'
CTS_NUM_TESTS_FAILED = 'CTS_NUM_TESTS_FAILED'
CTS_NUM_TESTS_NOT_EXECUTED = 'CTS_NUM_TESTS_NOT_EXECUTED'
CTS_REGEXES = (
        (re.compile('.*- INFO - copy CTS log from .* to .*/CTS_test/(.*)'),
         (CTS_LOG_DIR,)),
        (re.compile('.* Pass: (\d+), Fail: (\d+), Not Executed: (\d+).*'),
         (CTS_NUM_TESTS_PASSED, CTS_NUM_TESTS_FAILED,
          CTS_NUM_TESTS_NOT_EXECUTED)),
)


# Find and parse the build.prop file.
def find_and_parse_build_prop(log_dir):
    """Finds a build.prop file and parses it to get all the goodies inside.
    Args:
        log_dir: A zipfile.ZipFile to look inside.
    Returns: See re_match_one_in_file for type.
    """
    files = [x for x in log_dir.namelist() if x.endswith('build.props')]
    if not files or len(files) > 2:
        raise RuntimeError('Unexpected number of build.prop files: %s' %
                           str(files))

    with log_dir.open(files[0], 'r') as f:
        data = json.load(f)
        return data


_LOG_TIMESTAMP_RE = re.compile('([0-9]+)-([0-9]+)-([0-9]+) '
                               '([0-9]+):([0-9]+):([0-9]+),([0-9]+)')
def parse_log_timestamp(ts):
    """Parses the timestamp |ts| dropped by buildbot slave.

    Returns: datetime.datetime.
    """
    m = _LOG_TIMESTAMP_RE.match(ts)
    if m is None:
        return None

    try:
        print(m.groups()[6])
        return datetime.datetime(
                *[int(m.groups()[i]) for i in range(6)],
                microsecond=int(m.groups()[6])*1000)
    except ValueError:
        return None


def bq_format_timestamp(ts):
    """Format a datetime.datetime to a bigquery friendly string."""
    if ts is None:
        return None
    return ts.strftime('%Y-%m-%d %H:%M:%S.%f')


# We currently ignore timezone information.
_SQL_TIMESTAMP_RE = re.compile('([0-9]+)-([0-9]+)-([0-9]+) '
                               '([0-9]+):([0-9]+):([0-9]+)(?:.([0-9]+))?.*')
def bq_parse_timestamp(ts):
    """Parse an SQL TIMESTAMP string into datetime.datetime."""
    if ts is None or not ts:
        return None
    m = _SQL_TIMESTAMP_RE.match(ts)
    ms = 0
    if m.groups()[6] is not None:
        ms = m.groups()[6]
        ms += (6 - len(ms)) * '0'
        ms = int(ms)
    return datetime.datetime(*[int(m.groups()[i]) for i in range(6)],
                             microsecond=ms)
