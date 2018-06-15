"""Derived class of unittest.TestCase which has contains console and file handler

   This class is intented to be a base class of specific test case classes
"""

import os
import re
import stat
import sys
import unittest
import logging
import subprocess
import time
import psutil
import csv
import platform
import tempfile
import traceback
import threading
import shutil
import ConfigParser
from emu_error import *
import emu_test.utils.emu_argparser as emu_argparser
import emu_test.utils.path_utils as path_utils
from subprocess import PIPE, STDOUT
from collections import namedtuple
import test_fingerprint
import test_homescreen


class AVDConfig(namedtuple('AVDConfig', 'api, alt_version, tag, abi, device, ram, gpu, classic, port, cts, ori')):
    """
    Creates a Name for a AVD based upon the passed in arguments.
    """
    __slots__ = ()

    def __str__(self):
        device = self.device if self.device != '' else 'defdev'
        for ch in [' ', '(', ')']:
            device = device.replace(ch, '_')
        suffix = ""
        if emu_argparser.emu_args.is_gts:
          suffix = "-GTS"
        elif self.cts:
          suffix = "-CTS"
        alt = '%s-' % self.alt_version if self.alt_version else ''
        return str("%s-%s%s-%s-%s-gpu_%s-api%s%s" % (self.tag, alt, self.abi,
                                                     device, self.ram, self.gpu,
                                                     self.api, suffix))

    def name(self):
        return str(self)


class LoggedTestCase(unittest.TestCase):
    """
    Base Class that all emulator testCases are derived from.
    Two loggers are provided for each class, and each logger has both a console and file logger.
        1. m_logger, used for script messages, that are indicating the status of the script.
        2. simple_logger, used for messages from external processes, keeps their original format
    """
    m_logger = None
    simple_logger = None

    def __init__(self, *args, **kwargs):
        super(LoggedTestCase, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        simple_formatter = logging.Formatter('%(message)s')

        file_name = '%s_%s.log' % (cls.__name__, time.strftime("%Y%m%d-%H%M%S"))

        cls.m_logger = cls.setupLogger(cls.__name__, file_name, log_formatter)
        cls.simple_logger = cls.setupLogger(cls.__name__+'_simple', file_name, simple_formatter)

    @classmethod
    def setupLogger(cls, logger_name, file_name, formatter):

        file_handler = logging.FileHandler(os.path.join(emu_argparser.emu_args.session_dir,
                                                        emu_argparser.emu_args.test_dir,
                                                        file_name))
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        # Redirect message to standard out, these messages indicate test progress, they don't belong to stderr
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, emu_argparser.emu_args.loglevel.upper()))

        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(file_handler)
        # If this is a PsqBootTestCase, we dont print to console.  This is to
        # minimize output that swarming server must parse.
        if cls.__name__ != 'PsqBootTestCase':
            logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)

        return logger

    @classmethod
    def tearDownClass(cls):
        # clear up log handlers
        def cleanup(logger):
            for x in list(logger.handlers):
                logger.removeHandler(x)
                x.flush()
                x.close()
        cleanup(cls.m_logger)
        cleanup(cls.simple_logger)


class EmuBaseTestCase(LoggedTestCase):
    """
    Base class for Emulator TestCase class
    Provide common base functions that will be used in derived emu test classes
    """
    def __init__(self, *args, **kwargs):
        super(EmuBaseTestCase, self).__init__(*args, **kwargs)
        self.boot_time = 0

    @classmethod
    def setUpClass(cls):
        super(EmuBaseTestCase, cls).setUpClass()

    def setUp(self):
        self.m_logger.info('Running - %s', self._testMethodName)

    def term_check(self, timeout):
        """Check if emulator process has terminated, return True if terminated else False"""
        for x in range(timeout):
            time.sleep(1)
            if self.find_emu_proc() is None:
                return True
        return False

    def find_emu_proc(self):
        """Return the first active emulator process, None if not found"""
        for proc in psutil.process_iter():
            try:
                """
                emulator.exe is simply a wrapper around the emulator process qemu.  That is why we filter it. 
                Qemu 1 is named emulator-<arch>, whereas Qemu 2 is named qemu-system-<arch>    
                """
                if proc.name() != "emulator.exe" \
                        and "crash-service" not in proc.name() \
                        and ("emulator" in proc.name() or "qemu-system" in proc.name()):
                    self.m_logger.debug("Found - %s, pid - %d, status - %s" % (proc.name(), proc.pid, proc.status()))
                    if proc.status() != psutil.STATUS_ZOMBIE:
                        return proc
            except psutil.NoSuchProcess:
                print "Exception Thrown.  No Such process error while searching for emulator instance."
                print traceback.format_exc()
                pass
        return None

    def kill_proc_by_name(self, proc_names):
        """
        Iterates over all active system processes (found via psutil.process_iter()) and searches for the proc_names
        passed.  If found, Calls kill() on the found psutil.Process
        :param proc_names: List of process names we wish to search for and kill.
        :return: None.
        """
        for x in psutil.process_iter():
            try:
                proc = psutil.Process(x.pid)
                # mips 64 use qemu-system-mipsel64, others emulator-[arch]
                if any([x in proc.name() for x in proc_names]):
                    if proc.status() != psutil.STATUS_ZOMBIE:
                        self.m_logger.info("kill_proc_by_name - %s, %s" % (proc.name(), proc.status()))
                        proc.kill()
            except psutil.NoSuchProcess:
                print "Exception Thrown as psutil says no such process."
                print traceback.format_exc()

    def launch_emu(self, avd):
        """
        Launches the emulator using the passed avd.  The avd is a string created by the AVDConfig.name() function.
        Contains 3 inner functions related to launching and reading logcat output.  We push logcat information into a
        file, and then read from that file, in order to prevent IO impacting main thread.
        :param avd:  Name of the AVD we want to launch the emulator with.
        :return:
        """
        def get_logcat_filepath():
            """
            Returns the filepath of the logcat file for this test.
            :return: Filepath of the logcat output file.
            """
            local_test_name = self.id().rsplit('.', 1)[-1]
            logcat_filepath = os.path.join(emu_argparser.emu_args.session_dir,
                                           emu_argparser.emu_args.test_dir,
                                           "%s_logcat.txt" % local_test_name)
            return logcat_filepath

        def launch_logcat_in_thread(logcat_filepath):
            """
            Launches a logcat instance in a new psutil.Popen() call.  Logcat output is directed to a txt file named
            "testcase_logcat.txt".  Called as a target to the threading library so this runs in its own thread, not as
            part of the main test thread.
            :param logcat_filepath: Location where we will write logcat output.
            :return: None.  Returns when emulator is no longer found.
            """
            with open(logcat_filepath, 'a') as output:
                local_test_name = self.id().rsplit('.', 1)[-1]
                logcat_proc = None
                while True:
                    if logcat_proc is None or logcat_proc.poll() is not None:
                        self.m_logger.info('Launching logcat for test %s at location %s' %
                                           (local_test_name, logcat_filepath))
                        output.flush()
                        output.write("----Starting logcat----\n")
                        output.flush()
                        adb_binary = path_utils.get_adb_binary()
                        logcat_proc = psutil.Popen([adb_binary, "logcat"], stdout=output, stderr=STDOUT)
                    time.sleep(10)
                    if not self.find_emu_proc():
                        self.m_logger.info('No emulator found, stopping logcat %s' % local_test_name)
                        break
                if logcat_proc:
                  try:
                    logcat_proc.terminate()
                  except:
                    # Could not terminate logcat; probably already dead.
                    print "Exception Thrown.  Logcat is not found even though it is expected."
                    print traceback.format_exc()
                    pass

        def readoutput_in_thread(filepath):
            """
            Reads the output of self.start_proc.stdout process into a file. Also prints output to logger.
            :param filepath: File we will read from.
            :return: None.
            """
            with open(filepath, 'a') as log_output:
                lines_iterator = iter(self.start_proc.stdout.readline, b"")
                for line in lines_iterator:
                    line = line.strip()
                    log_output.write(line)
                    # Just write everything back to builder as a heart-beat signal to avoid being killed
                    self.m_logger.info("Emulator Output - " + line)
                    if any(x in line for x in ["ERROR", "FAIL", "error", "failed", "FATAL"]) and not line.startswith('['):
                        self.m_logger.error(line)

        # Function execution starts below
        self.m_logger.info('Launching Emulator with AVD, ...: %s', str(avd))
        emulator_bin = emu_argparser.emu_args.emulator_exec
        launch_cmd = [emulator_bin, "-avd", str(avd), "-verbose", "-show-kernel", "-wipe-data"]
        if avd.gpu == "swiftshader":
            launch_cmd += ["-gpu", "swiftshader_indirect"]
        # arm/mips is quit slow, disable boot animation
        if 'arm' in str(avd) or 'mips' in str(avd):
            launch_cmd += ["-no-boot-anim"]
        # Launch emulator with "-dns-server 8.8.8.8"
        # For CTS test to make test_getByName in android.core.tests.libcore.package.libcore pass
        # Also windows and mac needs this to have network connection
        launch_cmd += ['-dns-server', '8.8.8.8']
        launch_cmd += ['-skip-adb-auth']
        test_name  = self.id().rsplit('.', 1)[-1]
        verbose_log_path = os.path.join(emu_argparser.emu_args.session_dir,
                                        emu_argparser.emu_args.test_dir,
                                        "%s_verbose.txt" % test_name)
        self.m_logger.info('Launching AVD, cmd: %s' % ' '.join(launch_cmd))
        self.start_proc = psutil.Popen(launch_cmd, stdout=PIPE, stderr=STDOUT)
        self.m_logger.info('Done Launching AVD, cmd: %s' % ' '.join(launch_cmd))

        self.m_logger.info('Create thread to read output of AVD, cmd: %s' % str(avd))
        t_launch = threading.Thread(target=readoutput_in_thread, args=[verbose_log_path])
        t_launch.start()
        self.m_logger.info('Done create thread to read output of AVD, cmd: %s' % str(avd))

        self.m_logger.info('Create thread to read logcat of AVD, cmd: %s' % str(avd))
        logcat_thread = threading.Thread(target=launch_logcat_in_thread, args=[get_logcat_filepath()])
        logcat_thread.start()
        self.m_logger.info('Done creating thread to read logcat of AVD, cmd: %s' % str(avd))
        self.m_logger.info('Return from launching AVD, ...: %s' % str(avd))

    def run_with_timeout(self, cmd, timeout):
        """
        Run the passed in command, with a max time of timeout.  The timeout is enforced by running the passed command
        in a new thread, and joining the thread back to main execution after timeout seconds.  If the thread still
        reports as alive we forcefully kill it.
        :param cmd: List. The command we will run in the new thread.
        :param timeout: The time we will wait before joining back the new thread.
        :return: Tuple of (return code, stdout, stderr).
        """
        thread_info = {'process': None, 'stdout': '', 'stderr': '', 'returncode': ''}

        def run_cmd():
            """
            Helper function that serves as threading start target.
            Uses parent function variable "thread_info" to pass information.
            """
            thread_info['process'] = psutil.Popen(cmd, stdout=PIPE, stderr=PIPE)
            (thread_info['stdout'], thread_info['stderr']) = thread_info['process'].communicate()
            thread_info['returncode'] = thread_info['process'].returncode

        print "Starting command with timeout: %s, cmd: %s" % (timeout, " ".join(cmd))
        thread = threading.Thread(target=run_cmd)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.m_logger.info('Command %s timeout reached. Force terminate.' % ' '.join(cmd))
            try:
                thread_info['process'].terminate()
                # The command could be a full filepath.  We want only the name of the binary.
                cmd_binary = os.path.basename(cmd[0])
                self.kill_proc_by_name([cmd_binary])
            except Exception as e:
                self.m_logger.error('Failed to terminate the command.')
                print 'Exception Thrown: ' + traceback.format_exc()
        return thread_info['returncode'], thread_info['stdout'], thread_info['stderr']

    def check_network_connectivity(self):
        """
        Calls into ADB to get 'dumpsys connectivity' output.  Parses this output to confirm network connectivity
        settings.
        :return: Boolean.  False if environment appears incorrect.  True otherwise.
        """
        adb_binary = path_utils.get_adb_binary()
        ret, stdout, stderr = self.run_with_timeout([adb_binary, 'shell', 'dumpsys', 'connectivity'], 60)
        numNetworkReg = r'Active default network: (?P<numNetworkStr>\d+)'
        numNetworkMatch = re.search(numNetworkReg, stdout)
        hasNumNetwork = numNetworkMatch and numNetworkMatch.group('numNetworkStr') > 0

        dnsSuccessReg = r'PROBE_DNS (.*) OK';
        dnsSuccess = re.search(dnsSuccessReg, stdout)

        if not hasNumNetwork or not dnsSuccess:
            self.m_logger.error('adb shell dumpsys connectivity returns: %s' % stdout)
            return False
        return True

    def launch_emu_and_wait(self, avd):
        """
        Attempts to launch the passed in AVD.  Emulator Binary and other system settings are contained within
        emu_argparser.emy_args.  The emulator is started in a separate thread.  The timeout that is passed in via
        emu_argparser.emu_args.expected_boot_time is the timeout value of the 'wait' -> it is not forever.
        For API P, we also check network connection.
        :param avd: AVD we wish to launch.
        :return: Boot time (in seconds) it took to get a fully booted emulator.
        """
        adb_binary = path_utils.get_adb_binary()
        self.run_with_timeout([adb_binary, 'kill-server'], 20)
        self.run_with_timeout([adb_binary, 'start-server'], 20)
        launcher_emu = threading.Thread(target=self.launch_emu, args=[avd])
        launcher_emu.start()
        start_time = time.time()
        completed = '0'
        counter = 0
        real_time_out = emu_argparser.emu_args.expected_boot_time
        # We wait 20 seconds after attempting to start the emulator before polling ADB.  This is because the ADB
        # Daemon can be unresponsive on some machines during the startup period with the device.
        time.sleep(20)
        stdout = None
        stderr = None
        # While loop implements the timeout check by constantly checking the current run time against timeout.
        while (time.time() - start_time) < real_time_out:
            # We use ADB to directly look at the emulator instance and see if its marked as booted.
            cmd = [adb_binary, 'shell', 'getprop', 'sys.boot_completed']
            try:
                (exit_code, stdout, stderr) = self.run_with_timeout(cmd, 10)
            except Exception:
                self.m_logger.error('Failed in call to ADB when looking for sys.boot_completed property.')
                print 'Exception Thrown: ' + traceback.format_exc()
                continue
            # We will print out a status message every 20 invocations.  Keeps the log updated without spamming.
            if counter % 20 is 0:
                self.m_logger.info('Boot Timeout Max is set to %s, current is %s'
                                   % (real_time_out, time.time() - start_time))
                self.m_logger.info('Ping AVD %s for boot completion. stdout: %s stderr: %s'
                                   % (str(avd), stdout.strip(), stderr.strip()))
            counter = counter + 1
            if exit_code is 0:
                completed = stdout.strip()
            if completed is "1":
                self.m_logger.info('AVD %s is fully booted.  getprop sys.boot_completed = 1' % str(avd))
                break
            time.sleep(1)
        if completed is not "1":
            self.m_logger.info('ADB Failed to detect a booted emulator and timeout has been reached.')
            self.m_logger.info('Command: %s')
            self.m_logger.info('stdout: %s' % stdout)
            self.m_logger.info('stderr: %s' % stderr)
            self.m_logger.error('AVD %s didn\'t boot up within %s seconds' % (str(avd), real_time_out))
            self.boot_time = -1
            raise TimeoutError(avd, real_time_out)
        self.boot_time = time.time() - start_time
        self.m_logger.info('AVD %s, boot time is %s' % (str(avd), self.boot_time))
        if 'apiP' in str(avd):
            network_succeeded = False
            # Spend 3 mins (180 seconds) to check for network
            for i in range(18):
                time.sleep(10)
                # Connectivity check for P
                network_succeeded = self.check_network_connectivity()
                if network_succeeded:
                    self.m_logger.info('Network check succeeded.')
                    break
            if not network_succeeded:
                raise Exception('Network check error.  Failed to parse proper output.')
            if 'wear' in str(avd) or 'tv' in str(avd) or 'car' in str(avd):
                # We do not perform a homescreen or fingerprint test for these images.
                self.m_logger.info("Detected 'wear', 'tv' or 'car' AVD.  Skip Homescreen / Fingerprint tests.")
            elif 'google_apis' in str(avd):
                # Perform a homescreen test first.
                self.m_logger.info("Begin homescreen test for phone device.")
                homescreen_succeeded = test_homescreen.do_homescreen_test()
                if homescreen_succeeded:
                    self.m_logger.info("Homescreen test for phone device succeeded.")
                else:
                    self.m_logger.info("Homescreen test for phone device failed.")
                # Perform a fingerprint test.
                self.m_logger.info("Begin fingerprint test for phone device.")
                fingerprint_succeeded = test_fingerprint.do_fingerprint_test()
                if not fingerprint_succeeded:
                    # for now, just issue some message, later will turn it into exception
                    self.m_logger.info("Fingerprint test for phone device failed.")
                    #raise Exception('Fingerprint check error')
                else:
                    self.m_logger.info("Fingerprint test for phone device succeeded.")
        launcher_emu.join(10)
        if not emu_argparser.emu_args.skip_adb_perf:
            self.run_adb_perf(avd)
        return self.boot_time

    def run_adb_perf(self, avd):
        """
        Performs an ADB test on the given AVD.  The test consists of calling ADB push/pull on .zip files and return the
        time that these operations take.  The small_file.zip is 21Mb.  The large_file.zip is 121Mb.
        :param avd: The AVD we will be performing the test on.
        :return: None.  Results are printed to self.m_logger
        """
        test_file = "large_file.zip"
        local_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "adb_test_data", test_file)
        file_size = os.path.getsize(local_path)
        device_path = "/data/local/tmp/%s" % test_file
        adb_binary = path_utils.get_adb_binary()
        push_cmd = [adb_binary, "push", local_path, device_path]
        pull_cmd = [adb_binary, "pull", device_path, "."]
        run_time = []
        for cmd in [push_cmd, pull_cmd]:
            try:
                start_time = time.time()
                (exit_code, stdout, stderr) = self.run_with_timeout(cmd, 600)
                # deduct 0.015 seconds for the overhead of sending adb command (this is arbitrarily chosen).
                elapsed_time = time.time() - start_time - 0.015
                calculated_speed = (file_size/1024)/elapsed_time
                speed = "%.0f KB/s" % calculated_speed
                self.m_logger.info('Cmd: %s, Time elapsed: %s, File size: %s, speed: %s'
                                   % (' '.join(cmd), elapsed_time, file_size, speed))
                if exit_code == 0:
                    run_time.append(speed)
                else:
                    self.m_logger.info('Failed to run adb performance test cmd: %s, exit_code: %s'
                                       % (' '.join(cmd), exit_code))
                    return
            except Exception as e:
                if os.path.isfile(test_file):
                    os.unlink(test_file)
                self.m_logger.error('Exception for run_with_timeout %s:' % ' '.join(cmd))
                print 'Exception Thrown: ' + traceback.format_exc()
                return
        if os.path.isfile(test_file):
            os.unlink(test_file)
        self.m_logger.info('AVD %s ADB Performance test, adb push: %s, adb pull: %s' % (str(avd), run_time[0], run_time[1]))

    def create_avd_config(self, avd_config):
        """
        Create .ini file and sdcard.img for new AVD. This is called after AVD folder creation and top level .ini
        creation.
        :param avd_config: AVDConfig instance.
        :return: None.
        """
        class AVDIniConverter:
            """
            Class to help with the AVDConfig <-> ini file conversion.
            """
            output_file = None

            def __init__(self, file_path):
                self.output_file = file_path

            def write(self, what):
                self.output_file.write(what.replace(" = ", "="))

        def set_val(config_parser, key, val):
            """
            Set the key->value pair in the "Common" area of the ConfigParser object passed.
            :param config_parser: ConfigParser object.
            :param key: Key we will set.
            :param val: Value of the key we will set.
            :return: None.
            """
            if val != '':
                config_parser.set('Common', key, val)

        def load_section(config_parser, target_section):
            """
            Load the passed target section from the passed config_parser object.
            :param config_parser: ConfigParser object.
            :param target_section:
            :return:
            """
            for conf in config.options(target_section):
                set_val(config_parser, conf, config_parser.get(target_section, conf))

        # AVD directory is located at $HOME/.android/avd/
        avd_dir = os.path.join(os.path.expanduser('~'), '.android', 'avd',
                               '%s.avd' % avd_config.name())
        dst_path = os.path.join(avd_dir, 'config.ini')
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 '..', 'config', 'avd_template.ini')
        config.read(file_path)
        tag_id_to_display = {
                             'android-car': 'Android Automotive',
                             'android-tv': 'Android TV',
                             'android-wear': 'Android Wear',
                             'chromeos': 'Chrome OS',
                             'default': 'Default',
                             'google_apis': 'Google APIs',
                             'google_apis_playstore': 'Google APIs Playstore'
                            }
        abi_to_cpu_arch = {
                           'x86': 'x86',
                           'x86_64': 'x86_64',
                           'arm64-v8a': 'arm64',
                           'armeabi-v7a': 'arm',
                           'mips': 'mips',
                           'mips64': 'mips64'
                          }
        load_section(config, avd_config.device)
        if avd_config.cts:
            load_section(config, 'cts')
        set_val(config, 'AvdId', avd_config.name())
        set_val(config, 'abi.type', avd_config.abi)
        set_val(config, 'avd.ini.displayname', avd_config.name())
        set_val(config, 'hw.cpu.arch', abi_to_cpu_arch[avd_config.abi])
        if avd_config.abi == 'armeabi-v7a':
            set_val(config, 'hw.cpu.model', 'cortex-a8')
        gpu = "no" if avd_config.gpu == "no" else "yes"
        set_val(config, 'hw.gpu.enabled', gpu)
        set_val(config, 'hw.ramSize', avd_config.ram)
        set_val(config, 'image.sysdir.1',
                'system-images/%s/%s/%s/' % (self.get_sub_dir(avd_config), avd_config.tag, avd_config.abi))
        set_val(config, 'tag.display', tag_id_to_display[avd_config.tag])
        set_val(config, 'tag.id', avd_config.tag)

        self.m_logger.info("Create config.ini file at: %s", dst_path)
        for section in config.sections():
            if section != 'Common':
                config.remove_section(section)

        # Write the file out.  We call out to ACDIniConverter to remove spaces around equals signs.
        with open(dst_path, 'w') as fout:
            config.write(AVDIniConverter(fout))
        # Read the file back into memory.  Then re-create file with the header row no longer present.
        # Between these actions we remove the file.  This is because Windows can have issues properly truncating.
        with open(dst_path, 'r') as fin:
            data = fin.read().splitlines(True)
        try:
            os.unlink(dst_path)
        except OSError:
            self.m_logger.error('Error removing config file while trying to remove header.')
            print traceback.format_exc()
        with open(dst_path, 'w') as fout:
            fout.writelines(data[1:])
        # Create the sdcard.img file for this AVD.
        try:
            img_path = os.path.join(avd_dir, 'sdcard.img')
            mksdcard_binary = path_utils.get_mksdcard_binary()
            create_img_cmd = [mksdcard_binary, config.get('Common', 'sdcard.size'), img_path]
            self.m_logger.info('Create sdcard.img for AVD. cmd: %s', ' '.join(create_img_cmd))
            stdout, stderr = psutil.Popen(create_img_cmd, stdout=PIPE, stderr=PIPE).communicate()
        except ConfigParser.NoOptionError:
            self.m_logger.exception('Failed to find sdcard.size. Check avd_template.ini')
            self.m_logger.error('stdout: %s, stderr: %s' % stdout, stderr)
            print "Exception Thrown: " + traceback.format_exc()
            pass
        except:
            self.m_logger.exception('Failed to create sdcard.img for AVD.')
            self.m_logger.error('stdout: %s, stderr: %s' % stdout, stderr)
            print "Exception Thrown: " + traceback.format_exc()
            pass

    def get_sub_dir(self, avd_config):
        """
        Return the directory name (just folder name) where the userdata.img file must exists for the given avd_config.
        :param avd_config: AVDConfig class instance.
        :return: Name of the directory (just folder name) where the userdata.img file must be.
        """
        return 'android-%s' % avd_config.api if avd_config.tag != 'chromeos' else 'chromeos-%s' % avd_config.alt_version

    def update_chromeos(self, version):
        """
        Updates the chromeos image we use to perform tests.  Chromeos images are not currently available via sdkmanager.
        Because of this, we download the most recent internal images from gs:// and unzip into the proper directory.
        Once chromeos is released via sdkmanager we do not need to perform this step anymore.
        :param version: Version of the chromeos image we wish to download from gs:// bucket.
        :return: Return Code of the final unzip process.
        """
        gsutil_path = path_utils.get_gsutil_path()
        dst_location = os.path.join(os.environ['ANDROID_SDK_ROOT'],
                                    "system-images", "chromeos-%s" % version, "chromeos")
        chromeos_tmp_dir = tempfile.mkdtemp(prefix="chromeos_gs_download")
        chromeos_tmp_zip = os.path.join(chromeos_tmp_dir, "chromeos-download.zip")
        cmd = ['python', gsutil_path, 'cp',
               'gs://chromeos-emulator-test/images/system-%s.zip' % version, chromeos_tmp_zip]
        self.m_logger.info('Downloading new chromeos image: ' % ' '.join(cmd))
        update_proc = psutil.Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = update_proc.communicate()
        self.simple_logger.debug(stdout)
        self.simple_logger.debug(stderr)
        self.m_logger.debug('Return value of gsutil command: %s' % update_proc.poll())
        shutil.rmtree(dst_location, ignore_errors=True)
        os.makedirs(dst_location)
        cmd = ['unzip', chromeos_tmp_zip, '-d', dst_location]
        self.m.logger.info('Unzipping new chromeos image: %s' % ' '.join(cmd))
        unzip_proc = psutil.Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = unzip_proc.communicate()
        self.simple_logger.debug(stdout)
        self.simple_logger.debug(stderr)
        self.m_logger.debug('Return value of unzip proc: %s' % unzip_proc.poll())
        os.unlink(chromeos_tmp_zip)
        shutil.rmtree(chromeos_tmp_dir, ignore_errors=True)
        return unzip_proc.poll()

    def create_avd(self, avd_config):
        """
        Create AVD, overwriting old AVD if it exists.  We must do this, as when we create AVD's for system-images, we
        need to be sure we always use the newest downloaded image properly.  If we do not, and Windows has an issue
        removing a older file, we would end up using the wrong image, as the older AVD would still be present.
        :param avd_config: Configuration representing the AVD we wish to create.
        :return: Return code of the AVD create process.
        """
        def try_create_with_sdk():
            """
            Create AVD using the android command line tool.
            :return: Return code of android command line tool.
            """
            avdmanager_binary = path_utils.get_avdmanager_binary()
            avd_abi = "%s/%s" % (avd_config.tag, avd_config.abi)
            api_target = avd_config.api
            if "google" in avd_config.tag:
                avd_target = "Google Inc.:Google APIs:%s" % api_target
            else:
                avd_target = "android-%s" % api_target
            create_cmd = [avdmanager_binary, "create", "avd", "--force",
                          "--name", avd_name, "--target", avd_target,
                          "--abi", avd_abi]
            self.m_logger.info('Create AVD, cmd: %s' % ' '.join(create_cmd))
            avd_proc = psutil.Popen(create_cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
            stdout, stderr = avd_proc.communicate(input='\n')
            self.simple_logger.debug(stdout)
            self.simple_logger.debug(stderr)
            if 'Error' in stderr:
                return -1
            return avd_proc.poll()

        def try_create_with_config(avd_config_instance):
            """
            Create a new AVD based on avd_config_instance.
            Steps:
                1. Check system image installed userdata.img
                2. If there is existing AVD with this name, remove existing directory
                3. Create [AVD NAME].ini file
                4. Create AVD directory
                config.ini is created if above steps pass
            :param avd_config_instance: AVDConfig instance.
            :return: Zero on creation success.  Nonzero on failure.
            """
            # AVD directory is located at $HOME/.android/avd/
            avd_base_dir = os.path.join(os.path.expanduser('~'), '.android', 'avd')
            avd_dir = os.path.join(avd_base_dir, '%s.avd' % avd_name)
            api_target = avd_config_instance.api
            if 'google' in avd_config_instance.tag:
                avd_target = 'Google Inc.:Google APIs:%s' % api_target
            else:
                avd_target = 'android-%s' % api_target
            # Step 1.  Check if the requested API image exists.  We cannot create AVD without necessary image.
            userdata_src = os.path.join(os.environ['ANDROID_SDK_ROOT'],
                                        'system-images', self.get_sub_dir(avd_config_instance),
                                        avd_config_instance.tag, avd_config_instance.abi, 'userdata.img')
            if not os.path.isfile(userdata_src):
                self.m_logger.error('The userdata.img file %s does not exist! Must be installed to continue.'
                                    % userdata_src)
                return 1
            # Step 2. If the destination directory already exists, remove it.
            if os.path.exists(avd_dir):
                def remove_readonly(func, path, excinfo):
                    """
                    On Windows, some of the files are read-only, so when rmtree() tries to
                    remove them, an exception is thrown.  We attempt to set read/write and retry
                    here.
                    """
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                self.m_logger.info('Existing AVD found at %s.  Removing.' % avd_dir)
                # On Windows machines, we sometimes get a permssion error when trying to remove this dir.
                # To work around this, we attempt to make sure the file isnt read-only.
                shutil.rmtree(avd_dir, onerror=remove_readonly)
            # Step 3. Create the AVD {avd_name}.ini file.
            ini_path = os.path.join(avd_base_dir, '%s.ini' % avd_name)
            self.m_logger.info("AVD .ini file path: %s" % ini_path)
            with open(ini_path, "w") as ini_file:
                ini_file.write('avd.ini.encoding=UTF-8\n')
                ini_file.write('path=%s\n' % avd_dir)
                ini_file.write('path.rel=%s\n' % os.path.join('avd', '%s.avd' % avd_name))
                ini_file.write('target=%s\n' % avd_target)
            # Step 4. Create AVD directory.
            try:
                self.m_logger.info('Attempting to create new AVD dir: %s' % avd_dir)
                os.makedirs(avd_dir)
            except Exception as e:
                self.m_logger.error('Unable to create avd directory.')
                print "Exception Thrown: " + traceback.format_exc()
            return 0
        # Function execution starts here.
        avd_name = str(avd_config)
        self.m_logger.info('Attempt to create AVD %s.' % avd_name)
        ret = try_create_with_config(avd_config)
        if ret == 1:
            # If we failed to create the AVD with a return of 1, we may be missing the required image.
            # Try to download it.
            api = avd_config.api
            self.install_sdk_package("platforms;android-%s" % api)
            if "google_apis_playstore" in avd_config.tag:
                self.install_sdk_package("system-images;android-%s;google_apis_playstore;%s"
                                         % (api, avd_config.abi))
            elif "google" in avd_config.tag:
                self.install_sdk_package("add-ons;addon-google_apis-google-%s" % api)
                self.install_sdk_package("system-images;android-%s;google_apis;%s"
                                         % (api, avd_config.abi))
            elif "wear" in avd_config.tag:
                self.install_sdk_package("system-images;android-%s;android-wear;%s"
                                         % (api, avd_config.abi))
            elif "tv" in avd_config.tag:
                self.install_sdk_package("system-images;android-%s;android-tv;%s"
                                         % (api, avd_config.abi))
            elif "car" in avd_config.tag:
                self.install_sdk_package("system-images;android-%s;android-car;%s"
                                         % (api, avd_config.abi))
            elif "chromeos" in avd_config.tag:
                self.update_chromeos(avd_config.alt_version)
            else:
                self.install_sdk_package("system-images;android-%s;default;%s"
                                         % (api, avd_config.abi))
            self.m_logger.info('Attempt number 2 at AVD creation now that package has been attempted to be installed.')
            ret = try_create_with_config(avd_config)
        # last step, create config.ini
        if ret != 0:
            self.m_logger.error('Failed to create AVD, even after attempting package install.')
        else:
            self.create_avd_config(avd_config)

        return ret

    def install_sdk_package(self, package):
        """
        Call out to sdkmanager to try and install the passed package.
        :param package: String that is the particular package we wish to try and install.
        :return: Return code of the sdkmanager command.
        """
        sdkmanager_binary = path_utils.get_sdkmanager_binary()
        cmd = [sdkmanager_binary, '%s' % package]
        self.m_logger.info('Attempt to install SDK package: %s' % ' '.join(cmd))
        install_proc = psutil.Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout, stderr = install_proc.communicate(input='y\n')
        self.simple_logger.debug(stdout)
        self.simple_logger.debug(stderr)
        self.m_logger.info('Return value of the sdkmanager call: %s', install_proc.poll())
        return install_proc.poll()

    def update_sdk(self):
        """
        Calls out to sdkmanager with '--update', which attempts to update all installed packages.
        :return: Return code of the sdkmanager command.
        """
        sdkmanager_binary = path_utils.get_sdkmanager_binary()
        cmd = [sdkmanager_binary, '--update']
        self.m_logger.info('Attempt to update SDK packages: %s', ' '.join(cmd))
        update_proc = psutil.Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout, stderr = update_proc.communicate(input='y\n')
        self.simple_logger.debug(stdout)
        self.simple_logger.debug(stderr)
        self.m_logger.info('Return value of the sdkmanager call: %s', update_proc.poll())
        return update_proc.poll()


def create_test_case_from_file(desc, testcase_class, test_func, variants=None):
    """
    TODO. Refactor and Restructure the below functions and input files.
    Create one or more test cases based on test configuration file.

    If the `variants` parameter is included as an iterable, creates multiple
    test cases, one for each variant, passing each variant as an extra parameter
    to `test_func`. This is used, for example, in the UI tests to create a
    separate test case for each test class.
    :param desc: Description of the testcase_class.
    :param testcase_class: The class to add the test cases to.
    :param test_func: The function to call.
    :param variants: Iterable.  If present, create test case for each variant.
    :return:
    """
    def get_port():
        """
        Get the port of the current running process.  Emulator is usually at 5554, so use that if none found.
        :return: Port we wish to use to communicate with emulator.
        """
        if not hasattr(get_port, '_port'):
            get_port._port = 5552
        get_port._port += 2
        return str(get_port._port)

    def valid_case(avd_config):
        """
        TODO.
        :param avd_config: AVDConfig class we are looking at.
        :return: Boolean.  True if comparison passes, False if comparison fails.
        """
        def fn_leq(x,y): return x <= y

        def fn_less(x,y): return x < y

        def fn_geq(x,y): return x >= y

        def fn_greater(x,y): return x > y

        def fn_eq(x,y): return x == y

        def fn_neq(x,y): return x != y

        op_lookup = {
            "==": fn_eq,
            "=": fn_eq,
            "!=": fn_neq,
            "<>": fn_neq,
            ">": fn_greater,
            "<": fn_less,
            ">=": fn_geq,
            "<=": fn_leq
            }
        if emu_argparser.emu_args.filter_dict is not None:
            for key, value in emu_argparser.emu_args.filter_dict.iteritems():
                if any([value.startswith(x) for x in ["==", "!=", "<>", ">=", "<="]]):
                    cmp_op = value[:2]
                    cmp_val = value[2:]
                elif any([value.startswith(x) for x in ["=", ">", "<"]]):
                    cmp_op = value[:1]
                    cmp_val = value[1:]
                else:
                    cmp_op = "=="
                    cmp_val = value
                if not op_lookup[cmp_op](getattr(avd_config, key), cmp_val):
                    print "Error.  Detected invalid case in filter_dict."
                    return False
        return True

    def create_test_case(avd_config, op, builder_name=None, pattern=None, variant=None):
        """

        :param avd_config:
        :param op: Operation we want to perform for this test.
        :param builder_name: Name of the builder that is performing this build.
        :param pattern: Filename pattern we use to create Test-Cases.  For example, 'test_boot*.' finds all files
            starting with test_boot and searches for valid UnitTest objects within them.
        :param variant: Iterable.  If present, create test case for each variant.
        :return:
        """
        if not is_cts and avd_config.gpu == "yes" and not is_ui:
            avd_config_swiftshader = avd_config._replace(gpu = "swiftshader_indirect")
            create_test_case(avd_config_swiftshader, op, variant=variant)
            if avd_config.api >= "19" and avd_config.api <= "25" and "x86" in avd_config.abi:
                avd_config_guestgpu = avd_config._replace(gpu = "guest")
                create_test_case(avd_config_guestgpu, op, variant=variant)

        if op == "S" or op == "" or not valid_case(avd_config):
            return

        # For console tests, pass the builder name to it.
        if pattern and 'console' in pattern:
            if variant is not None:
                func = lambda self: test_func(self, avd_config, builder_name, variant)
            else:
                func = lambda self: test_func(self, avd_config, builder_name)
        else:
            if variant is not None:
                func = lambda self: test_func(self, avd_config, variant)
            else:
                func = lambda self: test_func(self, avd_config)

        if op == "X":
            func = unittest.expectedFailure(func)
        # TODO: handle flakey tests
        elif op == "F":
            func = func
        qemu_str = "_qemu2"
        variant_str = "%s_" % variant if variant is not None else ""
        # Group test results by ClassName_AVD-type.
        test_name = "test_%s%s_test_%s%s" % (variant_str, str(avd_config), desc, qemu_str)
        setattr(testcase_class, test_name, func)

    # Function execution starts here.
    is_cts = True if desc == "cts" else False
    is_ui = True if desc == "ui" else False
    with open(emu_argparser.emu_args.config_file, "rb") as file:
        reader = csv.reader(file)
        for row in reader:
            # Skip the first line of the file.  It is only a Header for human readable viewing.
            if reader.line_num == 1:
                continue
            if reader.line_num == 2:
                idx = [i for i, j in enumerate(row) if j in emu_argparser.emu_args.builder_name]
                assert len(idx) == 1, "Unexpected builder name {0} in line {1}, config file: {1}".format(
                    emu_argparser.emu_args.builder_name, row, emu_argparser.emu_args.config_file)
                builder_idx = idx[0]
            else:
                if(row[0].strip() != ""):
                    api = row[0].split("API", 1)[1].strip()
                    if ':' in api:
                        api, alt_version = api.split(':', 2)
                    else:
                        alt_version = ''
                if(row[1].strip() != ""):
                    tag = row[1].strip()

                if(row[2].strip() != ""):
                    abi = row[2].strip()

                # P - config should be passing
                # X - config is expected to fail
                # S and everything else - Skip this config
                if builder_idx >= len(row) or builder_idx < 0:
                    continue

                op = row[builder_idx].strip().upper()
                if op in ["P", "X", "F"]:
                    device = row[3]
                    if row[4] != "":
                        ram = row[4]
                    else:
                        ram = "512" if device == "" else "1536"
                    if row[5] != "":
                        gpu = row[5]
                    else:
                        gpu = "yes" if api > "15" else "no"
                    ori = row[6].strip()
                    ori = "public" if ori == "" else ori
                    # For 32 bit machine, ram should be less than 768MB
                    if not platform.machine().endswith('64'):
                        ram = str(min([int(ram), 768]))
                    # As of b/80137917 we no longer test qemu 1 for any tests.
                    classic = "no"
                    if device == "":
                      device = "default"
                    avd_config = AVDConfig(api, alt_version, tag, abi, device, ram, gpu, classic,
                                           get_port(), is_cts, ori)
                    for variant in variants or [None]:
                        create_test_case(avd_config, op, emu_argparser.emu_args.builder_name,
                                         emu_argparser.emu_args.pattern, variant)
