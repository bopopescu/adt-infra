#!/usr/bin/env python
# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import json
import optparse
import os
import subprocess
import sys
import tempfile

BUILD_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(os.path.join(BUILD_ROOT, 'scripts'))
sys.path.append(os.path.join(BUILD_ROOT, 'third_party'))

from common import annotator
from common import chromium_utils
from common import main_cfg_utils

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
BUILD_LIMITED_ROOT = os.path.join(
    os.path.dirname(BUILD_ROOT), 'build_internal', 'scripts', 'subordinate')

PACKAGE_CFG = os.path.join(
    os.path.dirname(os.path.dirname(SCRIPT_PATH)),
    'infra', 'config', 'recipes.cfg')

@contextlib.contextmanager
def namedTempFile():
  fd, name = tempfile.mkstemp()
  os.close(fd)  # let the exceptions fly
  try:
    yield name
  finally:
    try:
      os.remove(name)
    except OSError as e:
      print >> sys.stderr, "LEAK: %s: %s" % (name, e)

def get_recipe_properties(factory_properties, build_properties,
                          main_overrides_subordinate):
  """Constructs the recipe's properties from buildbot's properties.

  This retrieves the current factory properties from the main_config
  in the subordinate's checkout (the factory properties handed to us from the
  main might be out of date), and merges in the build properties.

  Using the values from the checkout allows us to do things like change
  the recipe and other factory properties for a builder without needing
  a main restart.
  """
  main_properties = factory_properties.copy()
  main_properties.update(build_properties)

  mainname = main_properties.get('mainname')
  buildername = main_properties.get('buildername')
  subordinate_properties = {}
  if mainname and buildername:
    try:
      subordinate_properties = get_factory_properties_from_disk(
          mainname, buildername)
    except LookupError as e:
      if main_overrides_subordinate:
        print 'WARNING in annotated_run.py (non-fatal): %s' % e
      else:
        raise e

  properties = main_properties.copy()
  conflicting_properties = {}
  for name in subordinate_properties:
    if main_properties.get(name) != subordinate_properties[name]:
      conflicting_properties[name] = (main_properties.get(name),
                                   subordinate_properties[name])

  if conflicting_properties:
    print 'The following build properties differ between main and subordinate:'
    for name, (main_value, subordinate_value) in conflicting_properties.items():
      print ('  "%s": main: "%s", subordinate: "%s"' % (
          name,
          "<unset>" if (main_value is None) else main_value,
          subordinate_value))
    print ("Using the values from the %s." %
           ("main" if main_overrides_subordinate else "subordinate"))

  if not main_overrides_subordinate:
    for name, (_, subordinate_value) in conflicting_properties.items():
      properties[name] = subordinate_value

  return properties


def get_factory_properties_from_disk(mainname, buildername):
  main_list = main_cfg_utils.GetMains()
  main_path = None
  for name, path in main_list:
    if name == mainname:
      main_path = path

  if not main_path:
    raise LookupError('main "%s" not found.' % mainname)

  script_path = os.path.join(BUILD_ROOT, 'scripts', 'tools',
                             'dump_main_cfg.py')

  with namedTempFile() as fname:
    dump_cmd = [sys.executable,
                script_path,
                main_path, fname]
    proc = subprocess.Popen(dump_cmd, cwd=BUILD_ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    exit_code = proc.returncode

    if exit_code:
      raise LookupError('Failed to get the main config; dump_main_cfg %s'
                        'returned %d):\n%s\n%s\n'% (
                        mainname, exit_code, out, err))

    with open(fname, 'rU') as f:
      config = json.load(f)

  # Now extract just the factory properties for the requested builder
  # from the main config.
  props = {}
  found = False
  for builder_dict in config['builders']:
    if builder_dict['name'] == buildername:
      found = True
      factory_properties = builder_dict['factory']['properties']
      for name, (value, _) in factory_properties.items():
        props[name] = value

  if not found:
    raise LookupError('builder "%s" not found on in main "%s"' %
                      (buildername, mainname))

  if 'recipe' not in props:
    raise LookupError('Cannot find recipe for %s on %s' %
                      (buildername, mainname))

  return props


def get_args(argv):
  """Process command-line arguments."""

  parser = optparse.OptionParser(
      description='Entry point for annotated builds.')
  parser.add_option('--build-properties',
                    action='callback', callback=chromium_utils.convert_json,
                    type='string', default={},
                    help='build properties in JSON format')
  parser.add_option('--factory-properties',
                    action='callback', callback=chromium_utils.convert_json,
                    type='string', default={},
                    help='factory properties in JSON format')
  parser.add_option('--build-properties-gz',
                    action='callback', callback=chromium_utils.convert_gz_json,
                    type='string', default={}, dest='build_properties',
                    help='build properties in b64 gz JSON format')
  parser.add_option('--factory-properties-gz',
                    action='callback', callback=chromium_utils.convert_gz_json,
                    type='string', default={}, dest='factory_properties',
                    help='factory properties in b64 gz JSON format')
  parser.add_option('--keep-stdin', action='store_true', default=False,
                    help='don\'t close stdin when running recipe steps')
  parser.add_option('--main-overrides-subordinate', action='store_true',
                    help='use the property values given on the command line '
                         'from the main, not the ones looked up on the subordinate')
  return parser.parse_args(argv)


def update_scripts():
  if os.environ.get('RUN_SLAVE_UPDATED_SCRIPTS'):
    os.environ.pop('RUN_SLAVE_UPDATED_SCRIPTS')
    return False

  stream = annotator.StructuredAnnotationStream()
  git_cmd = 'git.bat' if os.name == "nt" else 'git'
  with stream.step('update_scripts') as s:
    fetch_cmd = [git_cmd, 'fetch', '--all']
    reset_cmd = [git_cmd, 'reset', '--hard', 'origin/emu-main-dev']
    if subprocess.call(fetch_cmd) != 0 or subprocess.call(reset_cmd) != 0:
      s.step_text('git update source failed!')
      s.step_warnings()
    s.step_text('git pull')

    os.environ['RUN_SLAVE_UPDATED_SCRIPTS'] = '1'

    # After running update scripts, set PYTHONIOENCODING=UTF-8 for the real
    # annotated_run.
    os.environ['PYTHONIOENCODING'] = 'UTF-8'

    return True


def clean_old_recipe_engine():
  """Clean stale pycs from the old location of recipe_engine.

  This function should only be needed for a little while after the recipe
  packages rollout (2015-09-16).
  """
  for (dirpath, _, filenames) in os.walk(
      os.path.join(BUILD_ROOT, 'third_party', 'recipe_engine')):
    for filename in filenames:
      if filename.endswith('.pyc'):
        path = os.path.join(dirpath, filename)
        os.remove(path)


def main(argv):
  opts, _ = get_args(argv)
  properties = get_recipe_properties(
      opts.factory_properties, opts.build_properties,
      opts.main_overrides_subordinate)

  clean_old_recipe_engine()

  # Find out if the recipe we intend to run is in build_internal's recipes. If
  # so, use recipes.py from there, otherwise use the one from build.
  recipe_file = properties['recipe'].replace('/', os.path.sep) + '.py'
  if os.path.exists(os.path.join(BUILD_LIMITED_ROOT, 'recipes', recipe_file)):
    recipe_runner = os.path.join(BUILD_LIMITED_ROOT, 'recipes.py')
  else:
    recipe_runner = os.path.join(SCRIPT_PATH, 'recipes.py')

  with namedTempFile() as props_file:
    with open(props_file, 'w') as fh:
      fh.write(json.dumps(properties))
    cmd = [
        sys.executable, '-u', recipe_runner,
        'run',
        '--workdir=%s' % os.getcwd(),
        '--properties-file=%s' % props_file,
        properties['recipe'] ]
    return subprocess.call(cmd)


def shell_main(argv):
  if update_scripts():
    return subprocess.call([sys.executable] + argv)
  else:
    return main(argv)


if __name__ == '__main__':
  sys.exit(shell_main(sys.argv))
