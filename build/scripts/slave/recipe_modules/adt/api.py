import os
import datetime
import traceback
import uuid
from recipe_engine import recipe_api


class AdtApi(recipe_api.RecipeApi):
    def __init__(self, **kwargs):
        super(AdtApi, self).__init__(**kwargs)

    def PythonTestStep(self, description, session_dir, test_dir, test_pattern, cfg_file, cfg_filter,
                       emulator_path, env, skip_adb_perf=False):
        buildername = self.m.properties['buildername']
        buildnum = self.m.properties['buildnumber']
        rev = self.m.properties['revision']
        build_dir = self.m.path['build']
        script_root = self.m.path.join(build_dir, os.pardir, 'emu_test')
        dotest_path = self.m.path.join(script_root, 'dotest.py')

        # To see definitions for all arguments, see emu_argparser.py.
        test_args = ['--loglevel', 'INFO',
                     '--emulator', emulator_path,
                     '--session_dir', session_dir,
                     '--test_dir', test_dir,
                     '--file_pattern', test_pattern,
                     '--config_file', self.m.path.join(script_root, 'config', cfg_file),
                     '--buildername', buildername,
                     '--filter', cfg_filter]
        if skip_adb_perf is True:
            test_args.append('--skip-adb-perf')
        if 'GTS' in description:
            test_args.append('--is-gts')
        with self.m.step.defer_results():
            stderr_backing_file = uuid.uuid4().hex
            deferred_step_result = self.m.python(description, dotest_path, test_args, env=env,
                                                 stderr=self.m.raw_io.output('err', stderr_backing_file),
                                                 step_test_data=lambda: self.m.raw_io.test_api.stream_output(
                                                     'PASS: UI_TestCase', stream='stderr'))
            if os.path.exists(stderr_backing_file): # pragma: no cover
                try:
                    os.unlink(stderr_backing_file)
                except:
                    pass
            res = True
            # Debug line to help us know that deferred step has properly returned.
            print "Deferred Step Return Code: " + str(deferred_step_result.is_ok)
            if not deferred_step_result.is_ok:  # pragma: no cover
                stderr_output = deferred_step_result.get_error().result.stderr
                lines = [line for line in stderr_output.split('\n')
                         if line.startswith('FAIL:') or line.startswith('TIMEOUT:')]
                # Do not show empty links for UI tests since UI tests create these links to display test reports later.
                if "UI" not in description:
                    for line in lines:
                        self.m.step.active_result.presentation.logs[line] = ''
                res = False
            else:
                stderr_output = deferred_step_result.get_result().stderr
            if "UI" in description:
                lines = [line for line in stderr_output.split('\n')
                         if line.startswith('FAIL:')
                         or line.startswith('PASS:')
                         or line.startswith('TIMEOUT:')]
                for line in lines:
                    test_method = line.split(',')[0]
                    self.m.step.active_result.presentation.links['[Report] ' + test_method] = \
                        self.m.path.join("..", "..", "..", "UI_Result", buildername.replace(" ", "_"),
                                         'build_%s-rev_%s' % (buildnum, rev), test_method.split(' ')[1]
                                         + '_report', "index.html")
            if "CTS" in description:
                self.m.step.active_result.presentation.links['View XML'] = \
                    self.m.path.join("..", "..", "..", "CTS_Result", buildername.replace(" ", "_"),
                                     'build_%s-rev_%s' % (buildnum, rev), "testResult.xml")
            if "GTS" in description:
                self.m.step.active_result.presentation.links['View XML'] = \
                    self.m.path.join("..", "..", "..", "GTS_Result", buildername.replace(" ", "_"),
                                     'build_%s-rev_%s' % (buildnum, rev), "xtsTestResult.xml")
            if "Console" in description:
                self.m.step.active_result.presentation.links['View XML'] = \
                    self.m.path.join("..", "..", "..", "Console_Result", buildername.replace(" ", "_"),
                                     'build_%s-rev_%s' % (buildnum, rev), "consoleTestResult.xml")

            if "UI" in description or "Console" in description:
                requestedDate = datetime.datetime.fromtimestamp(self.m.properties['requestedAt']).date()
                filename = "{}-{}-{}_{}".format(requestedDate.month, requestedDate.day,
                                                requestedDate.year, buildnum)
                # TODO(@harrisonding): add code for Windows
                modified_filename = "/tmp/{}".format(filename) if "Win" not in buildername else filename
                if not self.m.properties.get("TESTING"):  # pragma: no cover
                    f = open(modified_filename, "w+")
                    f.write(buildername + "\n")
                    f.write("PASSED" if res else "FAILED")
                    f.close()
