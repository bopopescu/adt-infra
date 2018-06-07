# This should be run from the emu_test directory.
import os, platform
import xml.etree.ElementTree as ElementTree
import emu_test.utils.emu_argparser as emu_argparser

# Must do this before the import below to satisfy a query on
# emu_argparser.emu_args.avd_list in the module init code of
# test_cts.test_cts.
emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
emu_argparser.emu_args.avd_list = []

from test_cts.test_cts import CTSTestCase

def remove(path):
    if (os.path.isdir(path)):
        for f in os.listdir(path):
            remove(os.path.join(path, f))
        os.rmdir(path)
    elif os.path.isfile(path):
        os.remove(path)

cur_dir = os.getcwd()
fake_cts_path = os.path.join(cur_dir, 'test_cts', 'tests', 'fake_cts.sh')

test_dir_path = os.path.join('/tmp', 'test_run_cts_subplan')
remove(test_dir_path)
os.mkdir(test_dir_path)

subplan_results_dir = os.path.join('/tmp', 'fake_cts_output')
remove(subplan_results_dir)
os.mkdir(subplan_results_dir)

session_dir_path = os.path.join(test_dir_path, 'session')
os.mkdir(session_dir_path)

emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
emu_argparser.emu_args.session_dir = session_dir_path
CTSTestCase.setUpClass()
test_case = CTSTestCase(methodName='dummyRunTest', for_test=True)

paths = { 'cts_exec_path' : fake_cts_path, 'subplan_results_dir' : subplan_results_dir }

res = test_case.run_cts_subplan_work(paths, None, 'CTSSubplan')

assert res[0] == 'CTSSubplan'
assert res[1] == '123'
assert res[2] == '88'
assert res[3] == '16'

remove(test_dir_path)
