# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

DEPS = [
  'chromium',
  'chromium_tests',
  'properties',
]

def RunSteps(api):
  mainname = api.properties.get('mainname')
  buildername = api.properties.get('buildername')

  api.chromium_tests.configure_build(mainname, buildername)
  update_step, main_dict, test_spec = \
     api.chromium_tests.prepare_checkout(mainname, buildername)
  #api.chromium_tests.compile(mainname, buildername, update_step, main_dict,
  #                           test_spec, out_dir='/tmp')
  api.chromium.compile(targets=['All'], out_dir='/tmp')

def GenTests(api):
  yield api.test('basic_out_dir') + api.properties(
      mainname='chromium.linux',
      buildername='Android Builder (dbg)',
      subordinatename='build1-a1',
      buildnumber='77457',
  )
