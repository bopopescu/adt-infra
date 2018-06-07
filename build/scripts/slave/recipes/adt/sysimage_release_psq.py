# Copyright (c) 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Recipe for system image release testing."""

import os
import re
import traceback

from common.presubmit.agent_lib import AgentLib
from common.presubmit.constants import Constants

DEPS = [
    'adt',
    'file',
    'gerrit',
    'path',
    'platform',
    'properties',
    'python',
    'raw_io',
    'step',
    'json',
]

MASTER_USER = 'user'
MASTER_IP = '172.27.213.40'

CPU_ARCH_TO_ABI = {
  'x86': 'x86',
  'x86_64': 'x86_64',
  'arm64': 'arm64-v8a',
  'armv7': 'armeabi-v7a',
  'mips': 'mips',
  'mips64': 'mips64'
}

ORI_TO_API = {
  'git_gb-emu-release': '10',
  'git_ics-mr1-emu-release': '15',
  'git_jb-emu-release': '16',
  'git_jb-mr1.1-emu-release': '17',
  'git_jb-mr2-emu-release': '18',
  'git_klp-emu-release': '19',
  'git_lmp-emu-release': '21',
  'git_lmp-mr1-emu-release': '22',
  'git_mnc-emu-release': '23',
  'git_nyc-emu-release': '24',
  'git_nyc-preview-release': '25',  # Preview
  'git_nyc-mr1-emu-release': '25',
  'git_oc-emu-release': '26',
  'git_oc-mr1-emu-release': '27'
}

# Variables needed to communicate with Gerrit REST API.
HOST = "https://googleplex-android-review.googlesource.com/"
# TODO: Assign platform-dependent value once Windows and Mac presubmit bots are up
COOKIE_PATH = os.path.join(os.path.expanduser('~'), '.gitcookies')
PROJECTS = [] # Intentionally empty since slave only calls verify() (i.e. does not query).
BRANCH = "studio-master-dev"
PATH = ".*"
agentLib = None
TESTING = "TESTING"

def RunSteps(api):
  global agentLib
  home_dir = os.path.expanduser('~')
  env_path = ['%(PATH)s']
  buildername = api.properties['buildername']
  file_list = api.properties[Constants.CHANGE_FILES].split(',')
  buildnum = api.properties['buildnumber']
  rev = api.properties['revision']
  log_dir = 'logs-build_%s-rev_%s' % (buildnum, rev)
  build_dir = api.path['build']
  script_root = api.path.join(build_dir, os.pardir, 'emu_test')
  init_bot_util_path = api.path.join(script_root, 'utils', 'emu_bot_init.py')
  image_util_path = api.path.join(script_root, 'utils', 'download_unzip_image.py')
  if not TESTING in api.properties: # pragma: no cover
    agentLib = AgentLib(HOST, COOKIE_PATH, PROJECTS, BRANCH, PATH)
  psq_job_url = 'https://goto.google.com/adt-sysimage-release-test/builds/%s' % buildnum

  # Set up environment
  if api.platform.is_mac: # pragma: no cover
    android_sdk_home = os.path.join(home_dir, 'Android', 'android-sdk-macosx')
  elif api.platform.is_linux:
    android_sdk_home = os.path.join(home_dir, 'Android', 'android-sdk-linux')
  elif api.platform.is_win: # pragma: no cover
    android_sdk_home = os.path.join(home_dir, 'Android', 'android-sdk')
    if api.platform.bits == 64:
      gnu_path = 'C:\\Program Files (x86)\\GnuWin32\\bin'
    else:
      gnu_path = 'C:\\Program Files\\GnuWin32\\bin'
    cygwin_path = 'C:\\cygwin\\bin'
    env_path = [gnu_path, cygwin_path] + env_path
  else:
    raise  # pragma: no cover

  android_sdk_home += "_image-builds"
  emulator_path = api.path.join(android_sdk_home, 'tools', 'emulator')

  android_tools_dir = os.path.join(android_sdk_home, 'tools')
  android_platform_dir = os.path.join(android_sdk_home, 'platform-tools')
  android_buildtools_dir = os.path.join(android_sdk_home, 'build-tools', '23.0.2')
  env_path += [android_tools_dir, android_platform_dir, android_buildtools_dir]
  env = {'PATH': api.path.pathsep.join(env_path),
         'ANDROID_SDK_ROOT': android_sdk_home,
         'ANDROID_HOME': android_sdk_home}

  if not TESTING in api.properties: # pragma: no cover
    api.gerrit.post(agentLib, 'Start to test releasing system images: ' + psq_job_url)

  # Initialize bot
  try:
    api.python('Initialize Bot', init_bot_util_path,
               ['--build-dir', api.path['slave_build'],
                '--props', api.json.dumps(api.properties.thaw()),
                '--log-dir', log_dir],
               env=env)
  except api.step.StepFailure as f: # pragma: no cover
    # Not able to delete some files, it won't be the fault of emulator
    # not a stopper to run actual tests
    # so set status to "warning" and continue test
    f.result.presentation.status = api.step.WARNING

  # Download and unzip images
  api.python("Download and Unzip Images", image_util_path,
             ['--file', api.properties[Constants.CHANGE_FILES],
              '--build-dir', build_dir],
             env=env)

  def generate_test_config(test_configs, test_builder):
    # The first line is not parsed by dotest.py actually. So, it could be anything.
    out_stream = 'Device Config\n'
    # Table header
    out_stream += 'API*,TAG*,ABI*,DEVICE,RAM,GPU,ORI,%s\n' % test_builder
    for config in test_configs:
      out_stream += '%s,%s,%s,%s,%s,%s,%s,P\n' \
                    % (config['api'], config['tag'], config['abi'], config['device'],
                       config['ram'], config['gpu'], config['ori'])
    return out_stream

  # Generate a test configruation file from the system images under testing
  test_configs = []
  invalid_test_configs = set()
  for file in file_list:
    # gs://android-build-emu-sysimage/builds/git_[project]-emu-release-linux-[sdk*]_[ABI]-[sdk*]/[revision]/[hash]/*.zip
    # For some branches, arch is not included in target name. It is armeabi-v7a by default.
    config_str = file[5:].split('/')[2]
    m = re.match('(.*)-linux-.*_(x86.*|arm.*|mips.*)-.*', config_str)
    # if the config does not match m, that means abi is 'armeabi-v7a' by default and it should match m2 below.
    m2 = re.match('(.*)-linux-.*', config_str)
    # Filter out invalid image path
    if m is None and m2 is None: # pragma: no cover
      invalid_test_configs.add(config_str)
      continue
    config = {}
    try:
      if m is not None: # pragma: no cover
        config['api'] = 'API ' + ORI_TO_API[m.group(1)]
        config['abi'] = CPU_ARCH_TO_ABI[m.group(2)]
        config['ori'] = m.group(1)
      elif m2 is not None: # pragma: no cover
        config['api'] = 'API ' + ORI_TO_API[m2.group(1)]
        config['abi'] = 'armeabi-v7a'
        config['ori'] = m2.group(1)
      config['tag'] = 'google_apis' if 'google' in config_str and 'addon' in config_str else 'default'
      config['device'] = 'Nexus 5'
      config['ram'] = 2048
      config['gpu'] = 'yes'
    except: # pragma: no cover
      invalid_test_configs.add(config_str)
      print traceback.print_exc()
      continue

    test_configs.append(config)

  test_builder = buildername.split('_')[0]
  config_file = api.path.join(script_root, 'config', 'config.csv')
  api.file.write(name='Generate Test Configuration',
                 path=config_file,
                 data=generate_test_config(test_configs, test_builder))
  for invalid_test_config in invalid_test_configs: # pragma: no cover
    api.step.active_result.presentation.logs['Invalid test config: %s' % invalid_test_config] = ''
  # Explicitly set this step status to warning if an invalid test config is identified.
  # It actually helps to find any branch typo error in yaml files (though its bid is valid).
  if invalid_test_configs: # pragma: no cover
    api.step.active_result.presentation.status = api.step.WARNING

  with api.step.defer_results():
    api.adt.PythonTestStep('Run System Image UI Test',
                           log_dir,
                           'UI_test',
                           'test_ui.*',
                           'config.csv',
                           # We run only x86 images for UI tests.
                           # Besides, UiAutomation framework only supports API 18 or plus.
                           '{"abi": "x86", "api": ">=18"}',
                           emulator_path,
                           env,
                           True)
    api.file.remove(name='Remove Test Configuration', path=config_file)

    log_util_path = api.path.join(script_root, 'utils', 'zip_upload_logs.py')
    logs_dir = '/home/user/buildbot/external/adt-infra/build/masters/master.client.adt/slave_logs/'
    upload_log_args = ['--dir', log_dir,
                       '--name', 'build_%s-rev_%s.zip' % (buildnum, rev),
                       '--ip', MASTER_IP,
                       '--user', MASTER_USER,
                       '--dst', '%s%s/' % (logs_dir, buildername),
                       '--build-dir', build_dir,
                       '--skiplog']
    api.python("Zip and Upload Logs", log_util_path, upload_log_args, env=env)

    if not TESTING in api.properties: # pragma: no cover
      api.gerrit.post(agentLib, 'Check system image release test results at: ' + psq_job_url)


def GenTests(api):
    def props(properties):
        return api.properties(**properties)

    yield (
            api.test('linux-sysimage-release-psq') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'CHANGE_FILES': 'gs://android-build-emu-sysimage/builds/git_klp-emu-release-linux-sdk_x86-sdk/2872501/c9298a8eafceed3b8fa11071ba63a3d18e17fd8e/sdk-repo-linux-system-images-2872501.zip,gs://android-build-emu-sysimage/builds/git_lmp-emu-release-linux-sdk_phone_x86-sdk/2781484/3b78ad294aa1cdefa4be663d4af6c80d920ec49e/sdk-repo-linux-system-images-2781484.zip',
                'CHANGE_ID': 'platform%2Ftools%2Fvendor%2Fgoogle~studio-master-dev~Ic16536ac454fba1a3a31277010ba38a48b16ab0f',
                'CHANGE_REVISION': 'd2d143b1b04f39eb9b3154f3ad6f076c6b2add01',
                'blamelist': [],
                'branch': 'all',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu System Image Release',
                'buildnumber': '516',
                'sysimage-release-psq': '4696395',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/masters/master.client.adt/slave_logs/',
                'mastername': 'client.adt',
                'project': 'sysimage-release-psq',
                'recipe': 'adt/sysimage_release_psq',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'sysimage_release_psq_scheduler',
                'slavename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/slave/Console_emu-master-dev',
                'TESTING': True,
            })
    )

