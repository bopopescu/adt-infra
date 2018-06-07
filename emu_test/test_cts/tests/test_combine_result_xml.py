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
rel_path_to_tests = os.path.join(cur_dir, 'test_cts', 'tests')
result_dir = os.path.join('/tmp', 'test_combine_result_xml')
remove(result_dir)
os.mkdir(result_dir)

session_dir = os.path.join(result_dir, 'session')
os.mkdir(session_dir)

emu_argparser.emu_args = emu_argparser.get_parser().parse_args()
emu_argparser.emu_args.session_dir = session_dir

result_xml_dir = os.path.join(result_dir, 'cts_combined_result')

# The shard size is 14 packages.

paths = { 'subplan_results_dir' : cur_dir }

CTSTestCase.combine_xml_files(paths, result_xml_dir, 'CTS',
                              [os.path.join(rel_path_to_tests, 'test_shard_a_res'),
                               os.path.join(rel_path_to_tests, 'test_shard_b_res')],
                              3, 2, 1)

# Check desired properties of the result.
result_xml_path = os.path.join(result_xml_dir, 'testResult.xml')
res_tree = ElementTree.parse(result_xml_path)
res_root = res_tree.getroot()

assert res_root.get('testPlan') == 'CTS'
assert res_root.get('starttime') == "Thu Jun 30 16:07:24 PDT 2016"
assert res_root.get('endtime') == "Thu Jun 30 16:12:13 PDT 2016"
summary = res_root.find('Summary')
assert summary.get('pass') == "3"
assert summary.get('failed') == "2"
assert summary.get('notExecuted') == "1"
assert len(res_root.findall('TestPackage')) == 2

remove(result_dir)
