"""This file is used to upload stats to GCS

The data that will be uploaded are whether the builds failed or passed on
Emulator Console Tests and System Image UI Tests
"""
import os
import argparse
import subprocess
import datetime


parser = argparse.ArgumentParser(description='Upload stats on Emulator Console Tests and System Image UI Tests')
parser.add_argument('--buildnum', type=int, action='store', default=0, dest='buildnum', help='Build Number')
parser.add_argument('--buildername', type=str, action='store', default='foo', dest='buildername', help='Builder Name')
parser.add_argument('--passed', action='store_true')
parser.add_argument('--test_type', action='store', type=str, default='console', dest='test_type', help='Test Type')
parser.add_argument('--platform', action='store', type=str, default='lin', dest='platform', help='Platform')
parser.add_argument('--timestamp', action='store', type=int, default=0, dest='timestamp', help='Build Date')
parser.add_argument('--build-dir', dest='build_dir', action='store', help='Path to Build directory')
args = parser.parse_args()

def create_date_format(date):
  return "{}-{}-{}".format(date.month, date.day, date.year)

def get_platform_type(platform):
  if platform == 'win':
    return "Windows"
  elif platform == 'mac':
    return "Mac"
  return "Linux"

def upload_to_gcs():
  def verbose_call(cmd):
    print 'Run command {}'.format(' '.join(cmd))
    subprocess.check_call(cmd)
  requested_date = datetime.datetime.fromtimestamp(args.timestamp).date()
  filename = '{}_{}'.format(create_date_format(requested_date), args.buildnum)
  gsutil_path = os.path.join(args.build_dir, 'third_party', 'gsutil', 'gsutil.py')

  cp_filename = '/tmp/{}'.format(filename) if args.platform != "win" else filename
  if os.path.isfile(cp_filename):
    if args.test_type == 'console':
      verbose_call(['python', gsutil_path, 'cp', cp_filename, 'gs://console_si_test_results/emu_console_tests/{}/{}'.format(
          get_platform_type(args.platform), filename)])
    if args.test_type == 'system_image_ui':
      verbose_call(['python', gsutil_path, 'cp', cp_filename, 'gs://console_si_test_results/si_ui_tests/{}/{}'.format(
          get_platform_type(args.platform), filename)])
    verbose_call(['rm', cp_filename])
  else:
    print "Uploading to GCS failed due to failure to find file"

  return 0


if __name__ == '__main__':
  exit(upload_to_gcs())
