import os
import argparse
import subprocess
import psutil
import zipfile
import shutil

parser = argparse.ArgumentParser(description='Download and unzip a list of files separated by comma')
parser.add_argument('--file', dest='remote_file_list', action='store',
                    help='string contains a list of remote files separated by comma')
parser.add_argument('--build-dir', action='store',
                    help='location of build directory')

args = parser.parse_args()


def get_dst_dir(remote_path):
  file_name = os.path.basename(remote_path)
  emulator_branches = ["emu-main-dev", "emu-2.7-release"]
  # sdk_google_phone contains the playstore system images.
  if file_name.startswith('sdk-repo-linux-system-images') or file_name.startswith('sdk-repo-linux-addon') \
      or file_name.startswith('sdk-repo-darwin-system-images') or file_name.startswith('sdk_google_phone'):
    branch_name = remote_path.split('/')[-4]
    if 'user' in branch_name and 'userdebug' not in branch_name:
      tag = 'google_apis_playstore'
    elif 'google_atv' in branch_name:
      tag = 'android-tv'
    elif 'google' in branch_name and 'addon' in branch_name:
      tag = 'google_apis'
    elif 'gphone' in branch_name:
      tag = 'google_apis'
    elif 'gwear' in branch_name:
      tag = 'android-wear'
    elif 'oc-mr1-car-support' in branch_name:
      tag = 'android-car'
    else:
      tag = 'default'
    if 'lmp-mr1' in branch_name:
      api = '22'
    elif 'mnc' in branch_name:
      api = '23'
    elif 'nyc-mr1' in branch_name:
      api = '25'
    elif 'nyc' in branch_name:
      api = '24'
    elif 'oc-mr1-car-support' in branch_name:
      api = '27'
    elif 'oc-mr1' in branch_name:
      api = '27'
    elif 'oc' in branch_name:
      api = '26'
    elif 'lmp' in branch_name:
      api = '21'
    elif 'klp' in branch_name:
      api = '19'
    elif 'gb-emu' in branch_name:
      api = '10'
    elif 'ics-mr1-emu' in branch_name:
      api = '15'
    elif 'jb-emu' in branch_name:
      api = '16'
    elif 'jb-mr1.1-emu' in branch_name:
      api = '17'
    elif 'jb-mr2-emu' in branch_name:
      api = '18'
    elif 'pi' in branch_name:
      api = 'P'
    elif 'aosp-main' in branch_name:
      api = 'P'
    elif 'main' in branch_name:
      api = 'P'

    else:
      raise ValueError("unsupported image %s", branch_name)
    return os.path.join(os.environ['ANDROID_SDK_ROOT'],
                        "system-images", "android-%s" % api, tag)
  else:
    for branch in emulator_branches:
      if branch in remote_path:
        return branch
  return None

def clean_emu_proc():
  print 'clean up any emulator process'
  for x in psutil.process_iter():
    try:
      proc = psutil.Process(x.pid)
      # mips 64 use qemu-system-mipsel64, others emulator-[arch]
      if "emulator" in proc.name() or "qemu-system" in proc.name():
        print "trying to kill - %s, pid - %d, status - %s" % (proc.name(), proc.pid, proc.status())
        proc.kill()
    except:
      pass

def verbose_call(cmd):
  print "Run command %s" % ' '.join(cmd)
  subprocess.check_call(cmd)

def unzip_addon_dir(file_name, dst_dir):
  print file_name, dst_dir
  with open(file_name, 'rb') as fh:
    z = zipfile.ZipFile(fh)
    for name in z.namelist():
      if ("images/") in name and not name.endswith("images/"):
        base_name = os.path.basename(name)
        if not base_name:
          abi = os.path.basename(os.path.normpath(name))
          verbose_call(["mkdir", "-p", os.path.join(dst_dir,abi)])
          print "Found abi %s" % abi
          continue
        dst_path = os.path.join(dst_dir, abi, base_name)
        with z.open(name) as src, file(dst_path, "wb") as dst:
          print "unzip from %s to %s" % (name, dst_path)
          shutil.copyfileobj(src, dst)

gsutil_path = os.path.join(args.build_dir, 'third_party', 'gsutil', 'gsutil.py')
def get_file_list_cts():
    branches = [
        'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/',
        'gs://android-build-emu-sysimage/builds/git_mnc-emu-dev-linux-sdk_google_phone_x86-sdk_addon/',
                      ]
    file_list = []
    rev_list = []
    def find_latest(gspath):
        maxrev = 0
        proc = subprocess.Popen(['python', gsutil_path, 'ls', gspath], stdout=subprocess.PIPE)
        while True:
          output = proc.stdout.readline()
          if output == '' and proc.poll() is not None:
            break
          if output:
            output = output.strip()
            rev = output[output.rfind('/', 0, output.rfind('/'))+1:-1]
            maxrev = max(maxrev, int(rev))
        rev_list.append(str(maxrev))
        print "Found last build %s from %s" % (maxrev, gspath)
        subpath = '%s%s/' % (gspath, maxrev)
        proc = subprocess.Popen(['python', gsutil_path, 'ls', '-R', subpath], stdout=subprocess.PIPE)
        while True:
          output = proc.stdout.readline().strip()
          if output == '' and proc.poll() is not None:
            break
          if output and output.endswith('.zip') and 'sdk-repo-linux' in output:
            output = output.strip()
            file_list.append(output)
    for branch in branches:
        find_latest(branch)
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'config', 'rev.txt'), 'w') as ofile:
        ofile.write('-'.join(rev_list))
    return file_list

def download_and_unzip():
  clean_emu_proc()
  sdk_root = os.environ['ANDROID_SDK_ROOT']
  if 'image-builds' in sdk_root:
    image_dir = os.path.join(sdk_root, 'system-images')
    print 'Remove system image directory: ', image_dir
    verbose_call(['rm', '-rf', image_dir])
  if args.remote_file_list == "cts":
    file_list = get_file_list_cts()
  else:
    file_list = args.remote_file_list.split(',')

  for file_path in file_list:
    file_path = file_path.strip('\n')
    if file_path == '':
      continue
    dst_dir = get_dst_dir(file_path)
    file_name = file_path.split('/')[-1]
    try:
      verbose_call(['python', gsutil_path, 'cp', file_path, '.'])
      if dst_dir is not None:
        verbose_call(['mkdir', '-p', dst_dir])
        if 'x86_64' in file_path:
          verbose_call(['rm', '-rf', os.path.join(dst_dir,'x86_64')])
        elif 'x86' in file_path:
          verbose_call(['rm', '-rf', os.path.join(dst_dir,'x86')])
        elif 'armv7' in file_path:
          verbose_call(['rm', '-rf', os.path.join(dst_dir,'armeabi-v7a')])
        if 'addon' in file_name:
          unzip_addon_dir(file_name, dst_dir)
        else:
          if os.name == 'nt':
            # Windows needs to use 7z to fix pkcompat issues with default unzip
            verbose_call(['7z', 'x', '-aoa', file_name, ('-o%s' %  dst_dir)])
          else:
            verbose_call(['unzip', '-o', file_name, '-d', dst_dir])
        verbose_call(['rm', '-rf', file_name])
      else:
        raise ValueError('Error: Unknown branch!')
    except Exception as e:
      print "Error in download_and_unzip %r" % e
      return 1
  return 0

if __name__ == "__main__":
  exit(download_and_unzip())
