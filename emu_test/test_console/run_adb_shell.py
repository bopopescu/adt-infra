"""This script is to run adb shell instrumentation test."""

import subprocess
import sys
import time

from utils import util

launcher_class_name = '%s.Server' % util.MAIN_APK_PACKAGE
instrumentation_runner = 'android.support.test.runner.AndroidJUnitRunner'

num_trials = 1
while True:
  if num_trials is util.ADB_NUM_MAX_TRIALS:
    sys.exit(-1)
  try:
    print ('Run adb shell instrumentation test command, trial num: %s'
           % str(num_trials))
    res_run_adb_shell = subprocess.call(['adb', 'shell', 'am', 'instrument',
                                         '-w', '-e' 'class',
                                         launcher_class_name,
                                         ('%s.test/%s'
                                          % (util.MAIN_APK_PACKAGE,
                                             instrumentation_runner))])

    # Print GeoManagerService log for debugging geo test failure on API 23.
    adb_logcat = subprocess.Popen('adb logcat'.split(), stdout=subprocess.PIPE)
    print 'start: logcat'
    while True:
      line = adb_logcat.stdout.readline()
      if not line:
        break
      if line.find("GeoManagerService") != -1:
        print line
    adb_logcat.terminate()

    break
  except subprocess.CalledProcessError as err:
    print 'Subprocess call error: {0}'.format(err)
    time.sleep(util.ADB_TRIAL_WAIT_TIME_S)
    num_trials += 1
