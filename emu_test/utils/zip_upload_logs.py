import os
import argparse
import subprocess
import shutil

parser = argparse.ArgumentParser(description='Zip and upload log folders')

parser.add_argument('--dir', dest='log_dir', action='store',
                    help='local log directory')
parser.add_argument('--name', dest='zip_name', action='store',
                    help='name of zipped file - usually contains the build number')
parser.add_argument('--user', dest='remote_user', action='store',
                    help='remote user name')
parser.add_argument('--ip', dest='remote_ip', action='store',
                    help='remote ip')
parser.add_argument('--dst', dest='remote_dir', action='store',
                    help='remote directory')
parser.add_argument('--skiplog', dest='skiplog', action='store_true', help='skip uploading log')
parser.add_argument('--build-dir', dest='build_dir', action='store', help='path to build directory')
parser.add_argument('--iswindows', dest="is_windows", action='store_true', default=False,
                    help='treat file args as windows style')

args = parser.parse_args()

def zip_and_upload():

  def verbose_call(cmd):
    print "Run command %s" % ' '.join(cmd)
    subprocess.check_call(cmd)

  # The below is a special utility function to convert remote_dir to UNIX filepath.
  def convert_path_to_posix(path):
    return path.replace(os.path.sep, '/')

  try:
    if args.is_windows:
      zip_binary = ["7z", "a"]
    else:
      zip_binary = ["zip"]
    args.remote_dir = args.remote_dir.replace(" ", "_")
    remote_host = '%s@%s' % (args.remote_user, args.remote_ip)
    remote_path = '%s:%s' % (remote_host, args.remote_dir)
    gsutil_path = os.path.join(args.build_dir, 'third_party', 'gsutil', 'gsutil.py')
    builderName = os.path.basename(os.path.normpath(args.remote_dir))

    if args.skiplog is False:
      verbose_call(zip_binary + ['-r', args.zip_name, args.log_dir])
      verbose_call(['ssh', remote_host, 'mkdir -p %s' % args.remote_dir])
      verbose_call(['scp', args.zip_name, remote_path])

     # if it is emu psq test log, zip and upload to GCS
    if 'emu_psq_logs' in args.log_dir:
      print 'Running command in directory: %s' % (os.getcwd())

      verbose_call(zip_binary + ['-jr', args.zip_name, args.log_dir])
      emu_psq_gs_dst = 'gs://emu_psq_logs/%s/' % (args.zip_name[0:-4])
      verbose_call(['python', gsutil_path, 'cp', args.zip_name, emu_psq_gs_dst])
      # remove log zip files
      try:
        print "Delete log zip %s" % args.zip_name
        os.remove(args.zip_name)
      except Exception as e:
        print "Error in deleting log zip %r" % e

    # if it is adb stress test log, zip and upload to GCS
    if 'adb_stress_logs' in args.log_dir:
      print 'Running command in directory: %s' % (os.getcwd())
      verbose_call(zip_binary + ['-r', args.zip_name, args.log_dir])
      adb_stress_gs_dst = 'gs://adb_test_traces/%s/' % builderName
      verbose_call(['python', gsutil_path, 'cp', args.zip_name, adb_stress_gs_dst])
      # remove log zip files
      try:
        print "Delete log zip %s" % args.zip_name
        os.remove(args.zip_name)
      except Exception as e:
        print "Error in deleting log zip %r" % e

    # if cts result is available, upload to public_html directory
    for x in ['CTS', 'GTS']:
      cts_logdir = os.path.join(args.log_dir, '%s_test' % x, '%s_combined_result' % x.lower())
      if os.path.isdir(cts_logdir):
        cts_dst = os.path.join(args.remote_dir, "..", "..", "public_html", "%s_Result" % x, builderName)
        cts_dst = os.path.normpath(cts_dst)
        verbose_call(['ssh', remote_host, 'mkdir -p %s' % cts_dst])
        verbose_call(['scp', '-r', os.path.join(cts_logdir, ''), '%s:%s' %
                      (remote_host, os.path.join(cts_dst, args.zip_name[:-4]))])

    # if ui result is available, upload to public_html directory
    ui_logdir = os.path.join(args.log_dir, "UI_test")
    if os.path.isdir(ui_logdir):
      ui_dst = os.path.join(args.remote_dir, "..", "..", "public_html", "UI_Result", builderName)
      remote_path = os.path.join(ui_dst, args.zip_name[:-4])
      os.path.normpath(remote_path)
      if args.is_windows is True:
        remote_path = convert_path_to_posix(remote_path)
      verbose_call(['ssh', remote_host, 'mkdir -p %s' % remote_path])
      ui_gs_dst = 'gs://sysimage_test_traces/%s/%s' % (builderName, args.log_dir)
      for x in os.listdir(ui_logdir):
        # upload gradle report to the master
        if os.path.isdir(os.path.join(ui_logdir, x)) and x.endswith("_report"):
          saved_path = os.path.abspath(os.path.curdir)
          os.chdir(os.path.join(os.path.abspath(os.path.curdir), ui_logdir))
          verbose_call(['scp', '-r', x, '%s:%s' % (remote_host, remote_path)])
          os.chdir(saved_path)
        # upload bugreport, logcat, verbose, and details dir to GCS
        elif os.path.isdir(os.path.join(ui_logdir, x)) and x.endswith("_details"):
          path_name = os.path.join(ui_gs_dst, x[:-8])
          path_name = convert_path_to_posix(path_name) if args.is_windows else path_name
          verbose_call(['python', gsutil_path, 'cp', '-r', os.path.join(ui_logdir, x), path_name])
        elif x.endswith('_bugreport.txt') or x.endswith('_logcat.txt') or x.endswith('_verbose.txt'):
          path_name = os.path.join(ui_gs_dst, x[:x.rfind('_')], '')
          path_name = convert_path_to_posix(path_name) if args.is_windows else path_name
          verbose_call(['python', gsutil_path, 'cp', os.path.join(ui_logdir, x), path_name])

    # if console result is available, upload to public_html directory
    console_logdir = os.path.join(args.log_dir, "Console_test")
    if os.path.isdir(console_logdir):
        console_dst = os.path.join(args.remote_dir, "..", "..", "public_html", "Console_Result", builderName)
        console_dst = os.path.normpath(console_dst)
        if args.is_windows is True:
          console_dst = convert_path_to_posix(console_dst)
        verbose_call(['ssh', remote_host, 'mkdir -p %s' % console_dst])
        path_name = os.path.join(console_dst, args.zip_name[:-4])
        path_name = convert_path_to_posix(path_name) if args.is_windows else path_name
        verbose_call(['scp', '-r', os.path.join(console_logdir, ''), '%s:%s' %
                      (remote_host, path_name)])

    # remove log directory
    try:
      print "Delete directory %s" % args.log_dir
      shutil.rmtree(args.log_dir)
    except Exception as e:
      print "Error in deleting log directory %r" % e

  except Exception as e:
    print "Error in zip_and_upload %r" % e
    return 1

  return 0

if __name__ == "__main__":
  exit(zip_and_upload())
