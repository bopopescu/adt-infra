# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Recipe for emulator boot tests."""

from recipe_engine.types import freeze
import os
import shutil
import csv
import collections
from subordinate.email_watcher import EmailRecipeWatcher

DEPS = [
    'adt',
    'path',
    'platform',
    'properties',
    'python',
    'raw_io',
    'step',
    'json',
    'trigger',
]

# The emulator branches we currently poll.
EMULATOR_BRANCHES = ['emu-main-dev', 'emu-2.7-release']

MASTER_USER = 'user'
MASTER_IP = '172.27.213.40'

# Tuple that maps to columns in a *_cfg.csv file.  Determines what images we boot.
bootStep = collections.namedtuple('bootStep', 'description, filter')
# Dictionary that keys between git branch and the *_cfg.csv information we will use for that build.
BOOT_STEPS = {
        'emu-main-dev': bootStep('public', '{"ori": "public"}'),
        'emu-2.7-release': bootStep('public', '{"ori": "public"}'),
        'main': bootStep('main', '{"ori": "main"}'),
        'aosp': bootStep('aosp', '{"ori": "aosp"}'),
        'pi-dev': bootStep('PI', '{"ori": "pi"}'),
        "pi-car-dev": bootStep('PI_CAR', '{"ori": "pi-car"}'),
        'mnc-emu-dev': bootStep('MNC', '{"ori": "mnc"}'),
        'lmp-mr1-emu-dev': bootStep('LMP_MR1', '{"ori": "lmp-mr1"}'),
        'nyc-mr1-emu-dev': bootStep('NYC_MR1', '{"ori": "nyc-mr1"}'),
        'nyc-emu-dev': bootStep('NYC', '{"ori": "nyc"}'),
        'oc-mr1-car-support-release': bootStep('OC_MR1_CAR_SUPPORT', '{"ori": "oc-mr1-car-support"}'),
        'oc-emu-dev': bootStep('OC', '{"ori": "oc"}'),
        'oc-mr1-emu-dev': bootStep('OC_MR1', '{"ori": "oc-mr1"}'),
        'lmp-emu-dev': bootStep('LMP', '{"ori": "lmp"}'),
        'klp-emu-dev': bootStep('KLP', '{"ori": "klp"}'),
        'gb-emu-dev': bootStep('GB', '{"ori": "gb"}'),
        'ics-mr1-emu-dev': bootStep('ICS_MR1', '{"ori": "ics-mr1"}'),
        'jb-emu-dev': bootStep('JB', '{"ori": "jb"}'),
        'jb-mr1.1-emu-dev': bootStep('JB_MR1.1', '{"ori": "jb-mr1.1"}'),
        'jb-mr2-emu-dev': bootStep('JB_MR2', '{"ori": "jb-mr2"}'),
    }


def get_android_sdk_home(api, is_cross_build, is_cts):
    """Return the location of the Android SDK Folder this build will use.

    If we are testing a system-image, we will use the "_image-builds" directory, which is for temporary images.  If we
    are testing the emulator, we always test against the current production system-images in "_public".

    Args:
        api:  Buildbot API passed to RunSteps with buildbot main data.
        is_cross_build: Boolean indicating if this is a cross_build request.
        is_cts: Boolean indicating if this is a cts request.

    Returns:
        Path to the Android SDK Folder we will use for this run.
    """
    home_dir = os.path.expanduser('~')
    if api.platform.is_mac:
        android_sdk_home = os.path.join(home_dir, 'Android', 'android-sdk-macosx')
    elif api.platform.is_linux:
        android_sdk_home = os.path.join(home_dir, 'Android', 'android-sdk-linux')
    # On windows, we need cygwin and GnuWin for commands like, rm, scp, unzip
    else:
        android_sdk_home = os.path.join(home_dir, 'Android', 'android-sdk')
    if api.properties.get('project') in EMULATOR_BRANCHES and not is_cross_build and not is_cts:
        android_sdk_home += "_public"
    else:
        android_sdk_home += "_image-builds"
    return android_sdk_home


def create_env(api, android_sdk_home):
    """Populates the environment we need for the given run.  Platform dependent.

    Args:
        api:  Buildbot API passed to RunSteps with buildbot main data.
        android_sdk_home:  Path to the Android SDK Folder we will use for this run.

    Returns:
        Dictionary of the environment we need to run the current build.
    """
    home_dir = os.path.expanduser('~')
    env_path = ['%(PATH)s']  # Current Path.  We will add to this, not replace it outright.
    jdk_18 = os.path.join(home_dir, 'bin', 'jdk1.8.0_121', 'bin')
    android_tools_dir = os.path.join(android_sdk_home, 'tools')
    android_tools_bin_dir = os.path.join(android_sdk_home, 'tools', 'bin')
    android_platform_dir = os.path.join(android_sdk_home, 'platform-tools')
    android_buildtools_dir = os.path.join(android_sdk_home, 'build-tools', '23.0.2')
    env_path = env_path + [android_tools_dir, android_tools_bin_dir, android_platform_dir, android_buildtools_dir, jdk_18]
    if api.platform.is_win:
        # Just add both 32/64 bit bin directories.  No harm from PATH perspective and simpler.
        gnu_path64 = 'C:\\Program Files (x86)\\GnuWin32\\bin'
        gnu_path = 'C:\\Program Files\\GnuWin32\\bin'
        cygwin_path = 'C:\\cygwin\\bin'
        cygwin_path64 = 'C:\\cygwin64\\bin'
        java_path = "C:\\ProgramData\\Oracle\\Java\\javapath"
        env_path = env_path + [gnu_path, gnu_path64, cygwin_path, cygwin_path64, java_path]
    env = {'PATH': api.path.pathsep.join(env_path),
           'ANDROID_SDK_ROOT': android_sdk_home,
           'ANDROID_HOME': android_sdk_home}
    return env


def get_props(api, android_sdk_home, build_cache): # pragma: no cover
    """Read the build_cache file from disk and return the properties for the given build.

    Args:
        api: Buildbot API passed to RunSteps with buildbot main data.
        android_sdk_home: Location fo the Android SDK we are currently using.
        build_cache: File that contains written properties for reading, populated by subsequent run.

    Returns:
        Dictionary object that represents api.properties['properties'] for this build.
    """
    props = {'blamelist': api.properties.get('blamelist'),
             'file_list': '',
             'logs_dir': api.properties.get('logs_dir'),
             'buildername': '%s_cross-builds' % api.properties.get('buildername').rsplit('_', 1)[0],
             'triggered': 'True',
             'got_revision': api.properties.get('revision'),
             'revision': api.properties.get('revision')}
    last_build = {}
    if not api.properties.get("TESTING"):
        with open(build_cache, 'r') as csvfile:
            filereader = csv.reader(csvfile)
            for row in filereader:
                if row[0] in BOOT_STEPS:
                    last_build[row[0]] = [row[1], row[2]]
        emulators, steps = get_test_config(api.properties.get('project'), android_sdk_home, True)
        for k in last_build:
            if k in emulators:
                props['file_list'] += last_build[k][1] + ','
                props[k] = last_build[k][0]
            elif k in steps:
                props[k + '_file'] = last_build[k][1]
                props[k] = last_build[k][0]

    return props


def set_props(api, build_cache):
    """Writes out the build_cache file to be used by a subsequent run.  Cross Builds utilize this file.

    Args:
        api: Buildbot API passed to RunSteps with buildbot main data.
        build_cache: File to write out properties to for reading by subsequent run.
    """
    props = {}
    if not api.properties.get("TESTING"): # pragma: no cover
        if api.path.exists(build_cache):
            with open(build_cache, 'r') as csvfile:
                filereader = csv.reader(csvfile)
                for row in filereader:
                    props[row[0]] = [row[1], row[2]]
        props[api.properties.get('project')] = [api.properties.get('revision'), api.properties.get('file_list')]
        with open(build_cache, 'w') as csvfile:
            filewriter = csv.writer(csvfile)
            for line in props:
                filewriter.writerow([line, props[line][0], props[line][1]])


# Figure out which emulator to use, and which test steps to run.
# For case 1, system-image builds, use only public emulator, and run boot test for the changing branch.
# For case 2, emulator builds, use the triggering emulator branch, run public boot test.
# For case 3, cross builds, if triggering factor is emulator branch, then use that emulator branch, on all system
#   image other than public.
# For case 4, if changes are in system-image branch, need to check against all of known good emulator branches, and
#   on the triggering branch image.
def get_test_config(project, android_sdk_home, cross_build):
    # case 1
    if project not in EMULATOR_BRANCHES and not cross_build:
        emulator_branch_to_use = [android_sdk_home]
        steps_to_run = [project]
    # case 2
    elif project in EMULATOR_BRANCHES and not cross_build:
        emulator_branch_to_use = [project]
        steps_to_run = [project]
    # case 3
    elif project in EMULATOR_BRANCHES and cross_build:
        emulator_branch_to_use = [project]
        steps_to_run = [x for x in BOOT_STEPS if x not in EMULATOR_BRANCHES]
    # case 4
    else:
        emulator_branch_to_use = [x for x in EMULATOR_BRANCHES]
        steps_to_run = [project]
    return emulator_branch_to_use, steps_to_run


@EmailRecipeWatcher()
def RunSteps(api):
    buildername = api.properties.get('buildername')
    project = str(api.properties.get('project'))
    build_dir = api.path['build']
    buildnum = api.properties.get('buildnumber')
    rev = api.properties.get('revision')
    is_cts = 'CTS' in str(buildername)
    is_ui = 'UI' in str(buildername)
    is_console = "console" in str(api.properties.get('scheduler'))
    is_avd = 'AVD' in str(buildername)

    # A Cross build is building newest emulator target vs newest image targets.
    # Whenever a new emulator build comes in we auto-trigger a cross build as well.
    is_cross_build = api.properties.get('triggered')

    # Get the directory of the Android SDK folder
    android_sdk_home = get_android_sdk_home(api, is_cross_build, is_cts)

    # Setup our environment variables
    env = create_env(api, android_sdk_home)

    # Find emulator script based on build directory
    # Emulator scripts are located [project root]/emu_test
    script_root = api.path.join(build_dir, os.pardir, 'emu_test')
    image_util_path = api.path.join(script_root, 'utils', 'download_unzip_image.py')
    log_util_path = api.path.join(script_root, 'utils', 'zip_upload_logs.py')
    init_bot_util_path = api.path.join(script_root, 'utils', 'emu_bot_init.py')
    build_cache = api.path.join(script_root, 'config', 'build_cache.csv')  # csv file format: branch,revision,file_list
    log_dir = 'logs-build_%s-rev_%s' % (buildnum, rev)

    # For cts test, download both the emulator and system image files
    # triggering branch could be either emulator or system image
    if is_cts:
        set_props(api, build_cache)

    try:
        api.python('Initialize Bot', init_bot_util_path,
                   ['--build-dir', api.path['subordinate_build'],
                    '--props', api.json.dumps(api.properties.thaw()),
                    '--log-dir', log_dir],
                   env=env)
    except api.step.StepFailure as f:  # pragma: no cover
        # Not able to delete some files, it won't be the fault of emulator
        # not a stopper to run actual tests
        # so set status to "warning" and continue test
        f.result.presentation.status = api.step.WARNING

    try:
        # Path to the create_cl_list.py script
        create_cl_list_path = api.path.join(script_root, 'utils', 'create_cl_list.py')
        api.python('Create CL List', create_cl_list_path,
                   ['--poller', str(api.properties.get('blamelist')),
                    '--prevRevision', api.properties.get('prev_build'),
                    '--curRevision', api.properties.get('revision')],
                   env=env)
    except api.step.StepFailure as f: # pragma: no cover
        f.result.presentation.status = api.step.WARNING
    except TypeError: # pragma: no cover
        # This occurs when we fail to find 'prev_build' within the properties file.
        # We will continue execution ignoring this error for now.
        pass

    api.python("Download and Unzip Images", image_util_path,
               ['--file', api.properties.get('file_list') if api.properties.get('file_list') else "cts",
                '--build-dir', build_dir],
               env=env)

    if is_cts:
        rev_file_path = api.path.join(script_root, 'config', 'rev.txt')
        if not api.properties.get("TESTING"): # pragma: no cover
            with open(rev_file_path) as revfile:
                rev_str = revfile.read()
        else:
            rev_str = "foo"
        api.step('Rev emu-img %s' % rev_str, ['echo', rev_str])

    emulator_branch_to_use, steps_to_run = get_test_config(project, android_sdk_home, is_cross_build)

    # filter out unavailable branches
    steps_to_run = [x for x in steps_to_run if api.properties.get(x)]
    emulator_branch_to_use = [x for x in emulator_branch_to_use if
                              (api.properties.get(x) or x not in EMULATOR_BRANCHES)]

    with api.step.defer_results():
        for step in steps_to_run:
            if is_cross_build:
                api.python("Download Image - %s" % step, image_util_path,
                           ['--file', api.properties.get(step + '_file'),
                            '--build-dir', build_dir],
                           env=env)
            for emu_branch in emulator_branch_to_use:
                emulator_path = api.path.join(emu_branch, 'emulator', 'emulator')
                step_data = BOOT_STEPS[step]
                emu_desc = "sdk emulator" if emu_branch not in EMULATOR_BRANCHES else emu_branch
                if not is_cts and not is_ui and not is_console and not is_avd:
                    step_data = BOOT_STEPS[step]
                    api.adt.PythonTestStep('Boot Test - %s System Image - %s' % (step_data.description, emu_desc),
                                           log_dir,
                                           'boot_test_%s_sysimage-%s' % (step_data.description, emu_desc),
                                           'test_boot.*',
                                           'boot_cfg.csv',
                                           step_data.filter,
                                           emulator_path,
                                           env)
                elif is_ui:
                    step_data = BOOT_STEPS[step]
                    res = api.adt.PythonTestStep('Run Emulator UI Test',
                                                 log_dir,
                                                 'UI_test',
                                                 'test_ui.*',
                                                 'ui_cfg.csv',
                                                 step_data.filter,
                                                 emulator_path,
                                                 env,
                                                 True)
                    # Here we upload the data on whether the build passed or failed to GCS
                    upload_data_path = api.path.join(script_root, 'utils', 'upload_test_stats_to_gcs.py')
                    upload_data_args = ['--test_type', 'system_image_ui',
                                        '--buildnum', buildnum,
                                        '--buildername', api.properties['buildername'],
                                        '--timestamp', api.properties['requestedAt'],
                                        '--build-dir', build_dir,
                                        ]
                    if res and res.is_ok:  # pragma: no cover
                        upload_data_args.append('--passed')
                    upload_data_args.append('--platform')
                    if api.platform.is_linux:
                        upload_data_args.append('lin')
                    elif api.platform.is_mac:
                        upload_data_args.append('mac')
                    elif api.platform.is_win:
                        upload_data_args.append('win')
                    api.python("Upload Test Results to GCS", upload_data_path, upload_data_args, env=env)
                elif is_console:
                    res = api.adt.PythonTestStep('Run Emulator Console Test',
                                                 log_dir,
                                                 'Console_test',
                                                 'test_console.*',
                                                 'console_cfg.csv',
                                                 '{"gpu": "yes"}',
                                                 emulator_path,
                                                 env,
                                                 True)
                    # Here we upload the data on whether the build passed or failed to GCS
                    upload_data_path = api.path.join(script_root, 'utils', 'upload_test_stats_to_gcs.py')
                    upload_data_args = ['--test_type', 'console',
                                        '--buildnum', buildnum,
                                        '--buildername', api.properties['buildername'],
                                        '--timestamp', api.properties['requestedAt'],
                                        '--build-dir', build_dir,
                                        ]
                    if res and res.is_ok:  # pragma: no cover
                        upload_data_args.append('--passed')
                    upload_data_args.append('--platform')
                    if api.platform.is_linux:
                        upload_data_args.append('lin')
                    elif api.platform.is_mac:
                        upload_data_args.append('mac')
                    elif api.platform.is_win:
                        upload_data_args.append('win')
                    api.python("Upload Test Results to GCS", upload_data_path, upload_data_args, env=env)

                elif is_avd:
                    api.adt.PythonTestStep('Run AVD Launch Test',
                                           log_dir,
                                           'AVD_test',
                                           'launch_avd.*',
                                           'avd_cfg.csv',
                                           '{"gpu": "yes"}',
                                           emulator_path,
                                           env,
                                           True)

        if is_cts:
            emulator_path = api.path.join('emu-main-dev', 'emulator', 'emulator')
            api.adt.PythonTestStep('Run Emulator CTS Test',
                                   log_dir,
                                   'CTS_test',
                                   'test_cts.*',
                                   'cts_cfg.csv',
                                   '{}',
                                   emulator_path,
                                   env,
                                   True)

            api.adt.PythonTestStep('Run Emulator GTS Test',
                                   log_dir,
                                   'GTS_test',
                                   'test_cts.*',
                                   'cts_cfg.csv',
                                   '{}',
                                   emulator_path,
                                   env,
                                   True)

        logs_dir = '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/'
        upload_log_args = ['--dir', log_dir,
                           '--name', 'build_%s-rev_%s.zip' % (buildnum, rev),
                           '--ip', MASTER_IP,
                           '--user', MASTER_USER,
                           '--dst', '%s%s/' % (logs_dir, buildername),
                           '--build-dir', build_dir]
        if is_ui or is_console:
            upload_log_args.append('--skiplog')
        if api.platform.is_win:
            upload_log_args.append('--iswindows')
        api.python("Zip and Upload Logs", log_util_path, upload_log_args, env=env)

        # Always force a clean of the *_image-builds/ directory to save space.  A single image download can be ~18 GB
        # which we cannot leave on every machine.
        if 'image-builds' in android_sdk_home and not api.properties.get("TESTING"):  # pragma: no cover
            image_dir = os.path.join(android_sdk_home, 'system-images')
            shutil.rmtree(image_dir, True)

        # Trigger next CTS build, to make CTS builder run continuously
        if is_cts:
            api.trigger({
                'buildername': buildername,
                'got_revision': 'LATEST'
            })

    # If this build is triggered by scheduler, and it passes above steps
    # trigger build on cross builders
    if not is_cts and not is_ui and not is_console and not is_cross_build and not api.properties.get("TESTING"):  # pragma: no cover
        set_props(api, build_cache)
        api.trigger(get_props(api, android_sdk_home, build_cache))



def GenTests(api):
    def props(properties):
        return api.properties(**properties)

    yield (
            api.test('linux-emu-main-dev') +
            api.platform.name('linux') +
            api.platform.bits(32) +
            props({
                    'blamelist': ['emulator_linux_poller'],
                    'branch': 'Ubuntu',
                    'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                    'buildername': 'Linux emu-main-dev',
                    'buildnumber': '1090',
                    'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/4696395/7e4b04c674e12fb492b0834b0b6b1f769629d234103b3703c3e74aa17ffe8e19/sdk-repo-linux-emulator-4696395.zip',
                    'got_revision': '4696395',
                    'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                    'mainname': 'client.adt',
                    'prev_build': '4696278',
                    'project': 'emu-main-dev',
                    'recipe': 'adt/adt',
                    'repository': '',
                    'requestedAt': 1522746361,
                    'revision': '4696395',
                    'scheduler': 'emu_main_dev_scheduler',
                    'subordinatename': 'chromeos1-row3-rack3-host1',
                    'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/emu-main-dev',
                    'TESTING': True,
                    'emu-main-dev': '4696395',
            })
    )

    yield (
            api.test('mac-emu-main-dev') +
            api.platform.name('mac') +
            api.platform.bits(32) +
            props({
                'blamelist': ['emulator_mac_poller'],
                'branch': 'Mac',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Mac emu-main-dev',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-mac-sdk_tools_mac/4696395/ce060f3f471e3aa5da1b29425381514a1dc07e8cca1343dff2b4d93cbc7a3efc/sdk-repo-darwin-emulator-4696395.zip',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'prev_build': '4696278',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'emu_main_dev_scheduler',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/emu-main-dev',
                'TESTING': True,
                'emu-main-dev': '4696395',
            })
    )

    yield (
            api.test('win64-emu-main-dev') +
            api.platform.name('win') +
            api.platform.bits(64) +
            props({
                'blamelist': ['emulator_windows_poller'],
                'branch': 'Win',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Win64 emu-main-dev',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/4696395/7e4b04c674e12fb492b0834b0b6b1f769629d234103b3703c3e74aa17ffe8e19/sdk-repo-windows-emulator-4696395.zip',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'prev_build': '4696278',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'emu_main_dev_scheduler',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/emu-main-dev',
                'TESTING': True,
                'emu-main-dev': '4696395',
            })
    )

    yield (
            api.test('linux-cross-builds-emulator') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'aosp': '4696395',
                'aosp_file': 'gs://android-build-emu-sysimage/builds/aosp-main-linux-sdk_x86_64-sdk/4686993/b056c89ab4797b9b869396ed45a83fb658244dce1c4df5f0b558341e999e1dc8/sdk-repo-linux-system-images-4686993.zip,gs://android-build-emu-sysimage/builds/aosp-main-linux-sdk_x86-sdk/4686993/5c360765bdd9949f14cd395d9e2eb4f71bc52a7b16c1ce4ed1fb8ef2d1a39002/sdk-repo-linux-system-images-4686993.zip',
                'blamelist': ['emulator_linux_poller'],
                'branch': 'Ubuntu',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu cross-builds',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/4696395/7e4b04c674e12fb492b0834b0b6b1f769629d234103b3703c3e74aa17ffe8e19/sdk-repo-linux-emulator-4696395.zip,',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'parent_buildername': 'Ubuntu 14.04 HD 4400_sysimg-aosp',
                'parent_buildnumber': '516',
                'prev_build': '4696278',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'triggered': True,
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/cross-builds',
                'TESTING': True,
                'emu-main-dev': '4696395',
                'mnc-emu-dev_file': 'gs://android-build-emu-sysimage/builds/git_mnc-emu-dev-linux-sdk_google_phone_x86_64-sdk_addon/4666753/56c19893abc142ca533e77022e5828c13da3bb0d62faf5bbad5c2a9b0a3ac680/sdk-repo-linux-system-images-4666753.zip,gs://android-build-emu-sysimage/builds/git_mnc-emu-dev-linux-sdk_google_phone_x86-sdk_addon/4666753/78c88231a3e01959fa0097cc0a972eb1c48768357f91b65010d0c2e0f69a8a62/sdk-repo-linux-system-images-4666753.zip',
            })
    )

    yield (
            api.test('linux-cross-builds-sysimg') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'aosp' : '4696395',
                'aosp_file': 'gs://android-build-emu-sysimage/builds/aosp-main-linux-sdk_x86_64-sdk/4695504/bd9ef7aa641e91405b331552397f104be3e68d15475528e086b12372247e5b79/sdk-repo-linux-system-images-4695504.zip,gs://android-build-emu-sysimage/builds/aosp-main-linux-sdk_x86-sdk/4695504/9f61883fcb96811a5c6bde8bdf65987f6b3a9ec2a89ec2dba0903e68e77c9b9c/sdk-repo-linux-system-images-4695504.zip',
                'blamelist': ['sys_image_aosp_poller'],
                'branch': 'all',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu cross-builds',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/4696395/7e4b04c674e12fb492b0834b0b6b1f769629d234103b3703c3e74aa17ffe8e19/sdk-repo-linux-emulator-4696395.zip,',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'parent_buildername': 'Ubuntu 14.04 HD 4400_sysimg-aosp',
                'parent_buildnumber': '516',
                'prev_build': '4696278',
                'project': 'aosp',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'triggered': True,
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/cross-builds',
                'TESTING': True,
                'emu-main-dev': '4696395',
            })
    )

    yield (
            api.test('linux-sysimg-oc') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'blamelist': ['sys_image_oc_dev_poller'],
                'branch': 'Ubuntu',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu sysimg-oc',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_gphone_x86-sdk_addon/4695513/c79ac27430405771fe8249079eb3be15e8944f27ad07f68aea3b2974e29be7c0/sdk-repo-linux-system-images-4695513.zip,gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_google_atv_x86-sdk/4695513/31a293ea4bb784ec7e768811687523475bfd9107695d52068f86a665b78e8ace/sdk-repo-linux-system-images-4695513.zip,',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'prev_build': '4696278',
                'project': 'oc-emu-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4695513',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'scheduler': 'sysimg-oc',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/sysimg-oc',
                'TESTING': True,
                'oc-emu-dev': '4695513',
            })
    )

    yield (
            api.test('linux-ui') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'blamelist': ['sys_image_oc_dev_poller'],
                'branch': 'all',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu UI_sysimg-oc',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_gphone_x86-sdk_addon/4695513/c79ac27430405771fe8249079eb3be15e8944f27ad07f68aea3b2974e29be7c0/sdk-repo-linux-system-images-4695513.zip,gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_google_atv_x86-sdk/4695513/31a293ea4bb784ec7e768811687523475bfd9107695d52068f86a665b78e8ace/sdk-repo-linux-system-images-4695513.zip,',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'prev_build': '4696278',
                'project': 'oc-emu-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4695513',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'scheduler': 'sysimg-oc',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/sys_image_oc_dev_poller',
                'TESTING': True,
                'oc-emu-dev': '4695513',
            })
    )

    yield (
            api.test('win-ui') +
            api.platform.name('win') +
            api.platform.bits(64) +
            props({
                'blamelist': ['sys_image_oc_dev_poller'],
                'branch': 'all',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Win UI_sysimg-oc',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_gphone_x86-sdk_addon/4695513/c79ac27430405771fe8249079eb3be15e8944f27ad07f68aea3b2974e29be7c0/sdk-repo-linux-system-images-4695513.zip,gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_google_atv_x86-sdk/4695513/31a293ea4bb784ec7e768811687523475bfd9107695d52068f86a665b78e8ace/sdk-repo-linux-system-images-4695513.zip,',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'prev_build': '4696278',
                'project': 'oc-emu-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4695513',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'scheduler': 'sysimg-oc',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/sys_image_oc_dev_poller',
                'TESTING': True,
                'oc-emu-dev': '4695513',
            })
    )

    yield (
            api.test('mac-ui') +
            api.platform.name('mac') +
            api.platform.bits(64) +
            props({
                'blamelist': ['sys_image_oc_dev_poller'],
                'branch': 'all',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Mac UI_sysimg-oc',
                'buildnumber': '1090',
                'file_list': 'gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_gphone_x86-sdk_addon/4695513/c79ac27430405771fe8249079eb3be15e8944f27ad07f68aea3b2974e29be7c0/sdk-repo-linux-system-images-4695513.zip,gs://android-build-emu-sysimage/builds/git_oc-emu-dev-linux-sdk_google_atv_x86-sdk/4695513/31a293ea4bb784ec7e768811687523475bfd9107695d52068f86a665b78e8ace/sdk-repo-linux-system-images-4695513.zip,',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'prev_build': '4696278',
                'project': 'oc-emu-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4695513',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'scheduler': 'sysimg-oc',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/sys_image_oc_dev_poller',
                'TESTING': True,
                'oc-emu-dev': '4695513',
            })
    )

    yield (
            api.test('linux-Console') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'blamelist': ['emulator_linux_poller'],
                'branch': 'Ubuntu',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu Console_emu-main-dev',
                'buildnumber': '516',
                'got_revision': '4696395',
                'emu-main-dev': '4696395',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/4697226/141118a3891867ada68e8b6add4fd4a54bed001bb8a6d90a619bfc0b7feffafe/sdk-repo-linux-emulator-4697226.zip',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'console_emu-main-dev-scheduler',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/Console_emu-main-dev',
                'TESTING': True,
            })
    )

    yield (
            api.test('mac-Console') +
            api.platform.name('mac') +
            api.platform.bits(64) +
            props({
                'blamelist': ['emulator_mac_poller'],
                'branch': 'Mac',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Mac Console_emu-main-dev',
                'buildnumber': '516',
                'got_revision': '4696395',
                'emu-main-dev': '4696395',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-mac-sdk_tools_mac/4697226/141118a3891867ada68e8b6add4fd4a54bed001bb8a6d90a619bfc0b7feffafe/sdk-repo-mac-emulator-4697226.zip',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'console_emu-main-dev-scheduler',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/Console_emu-main-dev',
                'TESTING': True,
            })
    )

    yield (
            api.test('windows-Console') +
            api.platform.name('win') +
            api.platform.bits(64) +
            props({
                'blamelist': ['emulator_win_poller'],
                'branch': 'Win',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Win Console_emu-main-dev',
                'buildnumber': '516',
                'got_revision': '4696395',
                'emu-main-dev': '4696395',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-win-sdk_tools_win/4697226/141118a3891867ada68e8b6add4fd4a54bed001bb8a6d90a619bfc0b7feffafe/sdk-repo-win-emulator-4697226.zip',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'console_emu-main-dev-scheduler',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/Console_emu-main-dev',
                'TESTING': True,
            })
    )

    yield (
            api.test('linux-CTS') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'blamelist': [],
                'branch': '',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu CTS',
                'buildnumber': '7640',
                'got_revision': 'LATEST',
                'mainname': 'client.adt',
                'project': '',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': 'LATEST',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/CTS',
                'TESTING': True,
            })
    )

    yield (
            api.test('linux-AVD') +
            api.platform.name('linux') +
            api.platform.bits(64) +
            props({
                'blamelist': ['emulator_linux_poller'],
                'branch': 'Ubuntu',
                'buildbotURL': 'http://chromeos1-row3-rack2-host1.cros.corp.google.com:8200/',
                'buildername': 'Ubuntu AVD',
                'buildnumber': '516',
                'got_revision': 'LATEST',
                'emu-main-dev': '4696395',
                'file_list': 'gs://android-build-emu/builds/aosp-emu-main-dev-linux-sdk_tools_linux/4696395/7e4b04c674e12fb492b0834b0b6b1f769629d234103b3703c3e74aa17ffe8e19/sdk-repo-linux-emulator-4696395.zip',
                'got_revision': '4696395',
                'logs_dir': '/home/user/buildbot/external/adt-infra/build/mains/main.client.adt/slave_logs/',
                'mainname': 'client.adt',
                'project': 'emu-main-dev',
                'recipe': 'adt/adt',
                'repository': '',
                'requestedAt': 1522746361,
                'revision': '4696395',
                'scheduler': 'avd_test_scheduler',
                'subordinatename': 'chromeos1-row3-rack3-host1',
                'workdir': '/home/adt_build/Buildbot/adt-infra/build/subordinate/AVD',
                'TESTING': True,
            })
    )
