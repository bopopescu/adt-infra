"""Run CTS tests for emulator"""

import cts_results_parser as ctsparser
from test_cts_exclusions import cts_plans_current_exclusions

import json
import xml.etree.ElementTree as ElementTree
import os, platform
import unittest
import psutil
import shutil
import re
import sys
import threading
import time
from subprocess import PIPE,STDOUT
import emu_test.utils.emu_argparser as emu_argparser

from emu_test.utils.emu_testcase import EmuBaseTestCase, AVDConfig
import emu_test.utils.emu_testcase
api_to_android_version = {"24": "7.0",
                          "23": "6.0",
                          "22": "5.1",
                          "21": "5.0",
                          "19": "4.4",
                          "18": "4.3",
                          "17": "4.2",
                          "16": "4.1",
                          "15": "4.0",
                          "10": "2.3"}
class CTSTestCase(EmuBaseTestCase):
    def __init__(self, *args, **kwargs):
        if 'for_test' in kwargs:
            self.for_test = kwargs['for_test']
            kwargs.pop('for_test')
        else:
            self.for_test = False
        super(CTSTestCase, self).__init__(*args, **kwargs)

    # So we can instantiate a dummy CTSTestCase for testing of class functionality,
    # via CTSTestCase(methodname = 'dummyRunTest').
    def dummyRunTest(self):
        return

    @classmethod
    def setUpClass(cls):
        super(CTSTestCase, cls).setUpClass()

    def setUp(self):
        self.m_logger.info('Running - %s', self._testMethodName)

    def kill_emu_procs(self):
        if self.for_test:
            return
        def kill_proc_by_name(proc_names):
            for x in psutil.process_iter():
                try:
                    proc = psutil.Process(x.pid)
                    # mips 64 use qemu-system-mipsel64, others emulator-[arch]
                    if any([x in proc.name() for x in proc_names]):
                        if proc.status() != psutil.STATUS_ZOMBIE:
                            self.m_logger.info("kill_proc_by_name - %s, %s" % (proc.name(), proc.status()))
                            proc.kill()
                except psutil.NoSuchProcess:
                    pass

        self.m_logger.debug('First try - quit emulator by adb emu kill')
        kill_proc = psutil.Popen(["adb", "emu", "kill"])
        # check emulator process is terminated
        if not self.term_check(timeout=10):
            self.m_logger.debug('Second try - quit emulator by psutil')
            kill_proc_by_name(["emulator", "qemu-system"])
            result = self.term_check(timeout=10)
            self.m_logger.debug("term_check after psutil.kill - %s", result)

    def tearDown(self):
        # Emulator processes will be killed in the run_cts_subplan call
        # that started them.
        try:
            kill_proc_by_name(["crash-service"])
            psutil.Popen(["adb", "kill-server"])
        except:
            pass

    def launch_emu_and_wait(self, avd):
        # If we're testing the infrastructure, don't actually launch the emulator.
        if not self.for_test:
            super(CTSTestCase, self).launch_emu_and_wait(avd)
            self.m_logger.info("Wait for 120 seconds for emulator to fully boot up")
            time.sleep(120)

    @staticmethod
    def get_cts_root(avd):
        home_dir = os.path.expanduser('~')
        if emu_argparser.emu_args.is_gts:
            return os.path.join(home_dir, 'Android', 'GTS', 'android-xts')
        if emu_argparser.emu_args.cts_dir is not None:
            return emu_argparser.emu_args.cts_dir
        cts_home = os.path.join(home_dir, 'Android', 'CTS')
        cts_dir = "%s-%s" % (api_to_android_version[avd.api], avd.abi)
        return os.path.join(cts_home, cts_dir, 'android-cts')

    @staticmethod
    def get_cts_exec(avd):
        exec_name = 'xts-tradefed' if emu_argparser.emu_args.is_gts else 'cts-tradefed'
        return os.path.join(CTSTestCase.get_cts_root(avd), 'tools', exec_name)

    @staticmethod
    def get_cts_plan_dir(avd):
        if emu_argparser.emu_args.cts_plan is not None:
            return emu_argparser.emu_args.cts_plan
        return os.path.join(CTSTestCase.get_cts_root(avd), 'repository', 'plans')

    @staticmethod
    def get_emu_stable_plan(avd, plan):
        cur_exclusions = cts_plans_current_exclusions();
        if (plan in cur_exclusions):
            plan_exclusions = cur_exclusions[plan]
            plan_dir = CTSTestCase.get_cts_plan_dir(avd)
            plan_path = os.path.join(plan_dir, plan + '.xml')
            emu_stable_plan = plan + '-emu-stable'
            emu_stable_plan_path = os.path.join(plan_dir, emu_stable_plan + '.xml')
            tree = ElementTree.parse(plan_path)
            for entry in tree.findall('Entry'):
                test_package = entry.attrib['name']
                if test_package in plan_exclusions:
                    entry.set('exclude', ';'.join(plan_exclusions[test_package]))
            tree.write(emu_stable_plan_path)
            return emu_stable_plan
        else:
            return plan

    # shard_num is zero-based: (0 <= shard_num < num_shards)
    # This method, taking plan_dir as an argument, exposed for testing.
    # Requires that paths has 'plan_dir' and 'supblan_file_dir' attributes;
    # reads the input plan file from paths['plan_dir'] + plan + '.xml', and
    # writes the output to paths['subplan_file_dir'].
    @staticmethod
    def get_cts_subplan_work(paths, avd, plan, shard_num, num_shards):
        plan_path = os.path.join(paths['plan_dir'], plan + '.xml')
        plan_shard = plan + '_' + str(shard_num) + '_of_' + str(num_shards)
        plan_shard_path = os.path.join(paths['subplan_file_dir'], plan_shard + '.xml')
        tree = ElementTree.parse(plan_path)
        tree_root = tree.getroot()
        num_tests = len(tree_root)
        tests_per_shard = (num_tests + num_shards - 1) / num_shards
        # Remove the first shard_num * tests_per_shard elements.
        # Removing an element makes the index of every subsequent element
        # one less, so we always remove the first element.
        for i in range(0, shard_num * tests_per_shard):
            tree_root.remove(tree_root[0])
        # Now remove the Entries, whose index in the remaining list is
        # >= tests_per_shard.
        tests_remaining = num_tests - (shard_num * tests_per_shard)
        for i in reversed(range(tests_per_shard, tests_remaining)):
            tree_root.remove(tree_root[i])
        tree.write(plan_shard_path)
        return plan_shard

    @staticmethod
    def get_cts_subplan(avd, plan, shard_num, num_shards):
        plan_dir = CTSTestCase.get_cts_plan_dir(avd)
        return get_cts_subplan_work(cls, plan_dir, plan_dir,
                                    avd, plan, shard_num, num_shards)

    # Requires paths to have the following attributes:
    #   'cts_exec_path' : CTS executable
    #   'subplan_results_dir' : directory into which the output of the run is written.
    def run_cts_subplan_work(self, paths, avd, subplan):
        result_re = re.compile("^.*XML test result file generated at (.*). Passed ([0-9]+), Failed ([0-9]+), Not Executed ([0-9]+)")
        self.assertEqual(self.create_avd(avd), 0)
        self.launch_emu_and_wait(avd)
        exec_path = paths['cts_exec_path']
        if emu_argparser.emu_args.is_gts:
            cts_cmd = [exec_path, "run", "xts", "--plan", subplan]
        else:
            cts_cmd = [exec_path, "run", "cts", "--plan", subplan, "--disable-reboot"]
        # use "script -c" to force message flush, not available on Windows
        if platform.system() in ["Linux", "Darwin"]:
            cts_cmd = ["script", "-c", " ".join(cts_cmd)]

        vars = {'result_line': "",
                'cts_proc': None}

        def launch_in_thread():
            self.m_logger.info('executable path: ' + exec_path)
            vars['cts_proc'] = psutil.Popen(cts_cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
            lines_iterator = iter(vars['cts_proc'].stdout.readline, b"")
            for line in lines_iterator:
                line=line.strip()
                self.simple_logger.info(line)
                if re.match(result_re, line):
                    vars['result_line'] = line
                    self.m_logger.info("Send exit to cts_proc")
                    vars['cts_proc'].stdin.write('exit\n')

        self.m_logger.info('Launching cts-tradefed, cmd: %s', ' '.join(cts_cmd))
        t_launch = threading.Thread(target=launch_in_thread)
        t_launch.start()
        t_launch.join()

        def move_log(name):
            """Copy CTS result to log directory"""
            src_log_path = os.path.join(paths['subplan_results_dir'], name)
            dst_log_path = os.path.join(emu_argparser.emu_args.session_dir, name)
            self.m_logger.info("copy CTS log from %s to %s" % (src_log_path, dst_log_path))
            shutil.copytree(src_log_path, dst_log_path)
        try:
            if vars['result_line'] != "":
                log_name, pass_count, fail_count, skip_count = re.match(result_re, vars['result_line']).groups()
                move_log(log_name)
                return (log_name, pass_count, fail_count, skip_count)
            else:
                self.assertEqual('NA', '0')
                return None
        finally:
            # Kill this emulator instance
            self.kill_emu_procs()

    def run_cts_plan(self, avd):
        plan = "XTS" if emu_argparser.emu_args.is_gts else "CTS"
        plan_dir = CTSTestCase.get_cts_plan_dir(avd)
        exec_path = CTSTestCase.get_cts_exec(avd)
        paths = { 'cts_exec_path' : exec_path,
                  'plan_dir' : plan_dir,
                  'subplan_file_dir' : plan_dir,
                  'subplan_results_dir' :
                  os.path.join(os.path.dirname(exec_path),
                               '..', 'repository', 'results') }
        plan = self.get_emu_stable_plan(avd, plan)
        self.run_cts_plan_work(paths, avd, plan)

    @staticmethod
    def combine_xml_files(paths, combined_result_dir,
                          top_plan, cts_result_dirs, pass_count, fail_count, skip_count):
        total_tests = pass_count + fail_count + skip_count
        first = True
        result_name = 'xtsTestResult.xml' if emu_argparser.emu_args.is_gts else 'testResult.xml'
        xsl_name = 'xts_result.xsl' if emu_argparser.emu_args.is_gts else 'cts_result.xsl'
        for cts_result_dir in cts_result_dirs:
            tree = ElementTree.parse(
                os.path.join(paths['subplan_results_dir'], cts_result_dir, result_name))
            tree_root = tree.getroot()
            if first:
                combined_tree = tree
                combined_root = tree_root
                # Fix the plan name.
                combined_root.set('testPlan', top_plan)
                first = False
            else:
                combined_root.set('endtime', tree_root.get('endtime'))
                for pkg in tree_root.findall('TestPackage'):
                    combined_root.append(pkg)
        summary = combined_root.find('Summary')
        summary.set('failed', str(fail_count))
        summary.set('pass', str(pass_count))
        summary.set('notExecuted', str(skip_count))

        # The combined result XML file will need ancillary files such as
        # cts_results.css and cts_result.xsl files (and others).
        # These will be present in any result directory from a
        # subplan.  So copy the first of these directories as the
        # result, then we'll overwrite it's testResult.xml.
        shutil.copytree(os.path.join(paths['subplan_results_dir'],
                                     cts_result_dirs[0]),
                        combined_result_dir)

        # We need the XML file to have an xml-stylesheet declaration.
        # I was unable to find a way to make ElementTree.write add
        # one.  Therefore I will write the XML declaration and the
        # xml-stylesheet declaration first.  (There is a way to
        # getElementTree.write to write the XML declaration...but not
        # in a way that allows the xml-stylesheet declaration to be
        # written as the second element.)
        combined_result_path = os.path.join(combined_result_dir, result_name)
        with open(combined_result_path, 'w') as f:
            f.write("<?xml version='1.0' encoding='UTF-8' standalone='no' ?>\n")
            f.write("<?xml-stylesheet type='text/xsl'  href='%s'?>\n" % xsl_name)
            combined_tree.write(f)

    # Exposed for testing.
    # Requires paths to have entries:
    #  'cts_exec_path' : the CTS executable
    #  'plan_dir' : directory in which to find the CTS plan XML file.
    #  'subplan_results_dir' : directory into which the output of a subplan run is written.
    #  'subplan_file_dir' : directory into which to write the generated subplan XML files.
    def run_cts_plan_work(self, paths, avd, plan):
        # Shard the overall CTS plan into this many subplans.
        NumShards = 1 if emu_argparser.emu_args.is_gts else 10
        subplan_results = []
        for i in range(0, NumShards):
            subplan_results.append(
                self.run_cts_subplan_work(
                    paths, avd,
                    self.get_cts_subplan_work(paths, avd, plan, i, NumShards)))

        cts_results_dirs = []
        pass_count = 0
        fail_count = 0
        skip_count = 0
        for subplan_result in subplan_results:
            cts_results_dirs.append(subplan_result[0])
            pass_count += int(subplan_result[1])
            fail_count += int(subplan_result[2])
            skip_count += int(subplan_result[3])

        # Write a top-level xml file.
        testName = 'gts' if emu_argparser.emu_args.is_gts else 'cts'
        top_result_dir = os.path.join(emu_argparser.emu_args.session_dir, '%s_combined_result' % testName)
        CTSTestCase.combine_xml_files(paths, top_result_dir, plan,
                                      cts_results_dirs, pass_count, fail_count, skip_count)

        self._checkResults(paths, avd, fail_count, cts_results_dirs)

    def _formatSet(self, to_format):
        to_format_list = sorted(to_format)
        # Arbitrary limit on how many names we print.
        num_explicit_names = 15
        num_others = len(to_format_list) - num_explicit_names
        result = ''
        if num_others > 0:
            result += '(These + %d others) ' % num_others
        result += ', '.join(to_format_list[:num_explicit_names])
        return result

    def _checkResults(self, paths, avd, fail_count, cts_results_dirs):
        if fail_count == 0:
            return

        baseline = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'ctsTestCurrentFlakinessData.json')
        with open(baseline, 'r') as f:
            flakiness_data = json.load(f)
        if not flakiness_data:
            self.m_logger.warning('Found empty / corrupted flakiness data')
            return
        self.m_logger.debug('Loaded flakiness data with %d entries' %
                            len(flakiness_data))

        matches = [x for x in flakiness_data
                   if (x['systemImageApi'] == avd.api and
                       x['systemImageTag'] == avd.tag and
                       x['systemImageAbi'] == avd.abi)]
        ignored_fails = set()
        required_passes = set()
        fail_results = set(['flaky', 'bad', 'gotBroken'])
        pass_results = set(['good', 'gotFixed'])
        for target in matches:
            for result in target.get('ctsFlakinessRecords', []):
                full_name = result['fullName']
                flakiness_result = result['flakinessResult']
                if flakiness_result in fail_results:
                    ignored_fails.add(full_name)
                if flakiness_result in pass_results:
                    required_passes.add(full_name)
        # A test that is known to be good for some of the |matches|, but bad for
        # others should remain in |ignored_fails|, but not in |required_passes|.
        required_passes = required_passes - ignored_fails

        fails = set()
        passes = set()
        result_name = 'xtsTestResult.xml' if emu_argparser.emu_args.is_gts else 'testResult.xml'
        for cts_results_dir in cts_results_dirs:
            cts_results_file_path = os.path.join(paths['subplan_results_dir'], cts_results_dir, result_name);
            results = ctsparser.extract_results(cts_results_file_path)
            for result in results:
                full_name = ctsparser.format_full_name(result)
                if result['Result'] == 'fail':
                    fails.add(full_name)
                elif result['Result'] == 'pass':
                    passes.add(full_name)

        new_fails = fails - ignored_fails
        missing_passes = required_passes - passes

        self.m_logger.info('List of test fails that were ignored: %s' %
                           self._formatSet(ignored_fails & fails))
        if new_fails:
            self.m_logger.error('List of significant test failures '
                               '(i.e., why did this run go red): %s' %
                               self._formatSet(new_fails))
        if missing_passes:
            self.m_logger.error('List of missing test passes '
                               '(i.e., why did this run go red): %s' %
                                self._formatSet(missing_passes))
        self.assertEqual(0, len(new_fails) + len(missing_passes))

def create_test_case_for_avds():
    avd_name_re = re.compile("([^-]*)-(.*)-(.*)-(\d+)-gpu_(.*)-api(\d+)-CTS$")
    def create_avd_from_name(avd_str):
        res = avd_name_re.match(avd_str)
        assert res is not None
        tag, abi, device, ram, gpu, api = avd_name_re.match(avd_str).groups()
        avd_config = AVDConfig(api, tag, abi, device, ram, gpu, classic="no", port="", cts=True, ori="mnc")
        return avd_config

    def fn(avd_name):
        return lambda self: self.run_cts_plan(create_avd_from_name(avd_name))

    for avd in emu_argparser.emu_args.avd_list:
        if avd_name_re.match(avd):
            setattr(CTSTestCase, "test_cts_%s" % avd, fn(avd))

# TODO: create test case based on config file. Since we need to do some pre-work to run CTS, use static AVD at this time for simplicity.
emu_test.utils.emu_testcase.create_test_case_from_file("cts", CTSTestCase, CTSTestCase.run_cts_plan)

#create_test_case_for_avds()

if __name__ == '__main__':
    emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
    sys.argv[1:] = emu_args.unittest_args
    unittest.main()
