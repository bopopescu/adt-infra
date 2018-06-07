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

def remove_dir(dir):
    if (os.path.isdir(dir)):
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        os.rmdir(dir)

cur_dir = os.getcwd()
plan_dir = os.path.join(cur_dir, 'test_cts', 'tests')
result_dir = os.path.join('/tmp', 'test_subplan')
remove_dir(result_dir)
os.mkdir(result_dir)

paths = { 'plan_dir' : plan_dir, 'subplan_file_dir' : result_dir }

# The shard size is 14 packages.

CTSTestCase.get_cts_subplan_work(paths, None, 'CTS', 0, 10)
result0_path = os.path.join(result_dir, 'CTS_0_of_10.xml')
assert os.path.isfile(result0_path)
tree = ElementTree.parse(result0_path)
tree_root = tree.getroot()
assert len(tree_root) == 14
assert tree_root[0].get('name') == 'android.JobScheduler'
assert tree_root[13].get('name') == 'android.assist'

CTSTestCase.get_cts_subplan_work(paths, None, 'CTS', 2, 10)
result2_path = os.path.join(result_dir, 'CTS_2_of_10.xml')
assert os.path.isfile(result2_path)
tree = ElementTree.parse(result2_path)
tree_root = tree.getroot()
assert len(tree_root) == 14
assert tree_root[0].get('name') == 'android.core.tests.libcore.package.harmony_java_net'
assert tree_root[13].get('name') == 'android.core.tests.libcore.package.tests'

CTSTestCase.get_cts_subplan_work(paths, None, 'CTS', 9, 10)
result9_path = os.path.join(result_dir, 'CTS_9_of_10.xml')
assert os.path.isfile(result9_path)
tree = ElementTree.parse(result9_path)
tree_root = tree.getroot()
# The number of entries in the test file is not a factor of 10; last shard has one
# fewer.
assert len(tree_root) == 13
assert tree_root[0].get('name') == 'com.android.cts.opengl'
assert tree_root[12].get('name') == 'com.drawelements.deqp.gles31.copy_image_non_compressed'

#clean up
remove_dir(result_dir)
