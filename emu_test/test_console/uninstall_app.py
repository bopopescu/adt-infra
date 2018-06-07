"""This script is to run adb to uninstall apps."""

import subprocess
import sys
import time

from utils import util

test_apk_package = '%s.test' % util.MAIN_APK_PACKAGE

num_trials = 1
while True:
  if num_trials is util.ADB_NUM_MAX_TRIALS:
    sys.exit(-1)
  try:
    print ('Run adb shell to uninstall apps, trial num: %s' % str(num_trials))
    subprocess.call(['adb', 'uninstall', util.MAIN_APK_PACKAGE])
    subprocess.call(['adb', 'uninstall', test_apk_package])
    break
  except subprocess.CalledProcessError as err:
    print 'Subprocess call error: {0}'.format(err)
    time.sleep(util.ADB_TRIAL_WAIT_TIME_S)
    num_trials += 1
