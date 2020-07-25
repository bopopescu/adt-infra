# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Recipe for building Chromium and running WebRTC-specific tests with special
# requirements that doesn't allow them to run in the main Chromium waterfalls.
# Also provide a set of FYI bots that builds Chromium with WebRTC ToT to provide
# pre-roll test results.

DEPS = [
  'archive',
  'bot_update',
  'chromium',
  'chromium_android',
  'chromium_tests',
  'gclient',
  'json',
  'path',
  'platform',
  'properties',
  'python',
  'webrtc',
]


def RunSteps(api):
  webrtc = api.webrtc
  webrtc.apply_bot_config(webrtc.BUILDERS, webrtc.RECIPE_CONFIGS,
                          git_hashes_as_perf_revisions=True)

  if api.platform.is_win:
    api.chromium.taskkill()

  if api.properties.get('mainname') == 'chromium.webrtc.fyi':
    # Sync HEAD revisions for Chromium, WebRTC and Libjingle.
    # This is used for some bots to provide data about which revisions are green
    # to roll into Chromium.
    p = api.properties
    revs = {
      'src': p.get('parent_got_revision', 'HEAD'),
      'src/third_party/webrtc': p.get('parent_got_webrtc_revision', 'HEAD'),
      'src/third_party/libjingle/source/talk': p.get(
          'parent_got_libjingle_revision', 'HEAD'),
    }
    for path, revision in revs.iteritems():
      api.gclient.c.revisions[path] = revision

  webrtc.checkout()
  webrtc.cleanup()
  if webrtc.should_run_hooks:
    api.chromium.runhooks()

  if webrtc.should_build:
    webrtc.compile()
    if (api.properties.get('mainname') == 'chromium.webrtc.fyi' and
        api.chromium.c.TARGET_PLATFORM != 'android'):
      webrtc.sizes()

  if webrtc.should_upload_build:
    webrtc.package_build()
  if webrtc.should_download_build:
    webrtc.extract_build()

  if webrtc.should_test:
    with api.chromium_tests.wrap_chromium_tests(
        api.properties.get('mainname')):
      if api.chromium.c.TARGET_PLATFORM == 'android':
        api.chromium_android.run_test_suite(
            'content_browsertests',
            gtest_filter='WebRtc*',
            shard_timeout=30*60)
      else:
        webrtc.runtests()

  webrtc.maybe_trigger()


def _sanitize_nonalpha(text):
  return ''.join(c if c.isalnum() else '_' for c in text)


def GenTests(api):
  builders = api.webrtc.BUILDERS
  CR_REV = 'c321321'
  LIBJINGLE_REV = '1161aa63'
  WEBRTC_REV = 'deadbeef'

  def generate_builder(mainname, buildername, revision=None,
                       failing_test=None, suffix=None):
    suffix = suffix or ''
    bot_config = builders[mainname]['builders'][buildername]
    bot_type = bot_config.get('bot_type', 'builder_tester')

    if bot_type in ('builder', 'builder_tester'):
      assert bot_config.get('parent_buildername') is None, (
          'Unexpected parent_buildername for builder %r on main %r.' %
              (buildername, mainname))
    test = (
      api.test('%s_%s%s' % (_sanitize_nonalpha(mainname),
                            _sanitize_nonalpha(buildername), suffix)) +
      api.properties.generic(mainname=mainname,
                             buildername=buildername,
                             revision=revision,
                             parent_buildername=bot_config.get(
                                 'parent_buildername')) +
      api.platform(bot_config['testing']['platform'],
                   bot_config.get(
                       'chromium_config_kwargs', {}).get('TARGET_BITS', 64))
    )
    if bot_config.get('parent_buildername'):
      test += api.properties(parent_got_revision=CR_REV)

      if mainname.endswith('.fyi'):
        test += api.properties(parent_got_libjingle_revision=LIBJINGLE_REV,
                               parent_got_webrtc_revision=WEBRTC_REV)

    if mainname.endswith('.fyi'):
      test += api.properties(got_revision=CR_REV,
                             got_libjingle_revision=LIBJINGLE_REV,
                             got_webrtc_revision=WEBRTC_REV)
    if failing_test:
      test += api.step_data(failing_test, retcode=1)

    return test

  for mainname in ('chromium.webrtc', 'chromium.webrtc.fyi'):
    main_config = builders[mainname]
    for buildername in main_config['builders'].keys():
      # chromium.webrtc.fyi builders are triggered on WebRTC revisions and it's
      # passed as a build property to the builder. However it's ignored since
      # these builders only build 'HEAD' for Chromium, WebRTC and libjingle.
      # That means got_revision and parent_got_revision will still be a Chromium
      # Git hash for these builders.
      revision = WEBRTC_REV if mainname == 'chromium.webrtc.fyi' else CR_REV
      yield generate_builder(mainname, buildername, revision)

  # Forced build (not specifying any revision) and failing tests.
  mainname = 'chromium.webrtc'
  yield generate_builder(mainname, 'Linux Builder', suffix='_forced')

  buildername = 'Linux Tester'
  yield generate_builder(mainname, buildername, suffix='_forced_invalid')
  yield generate_builder(mainname, buildername, failing_test='browser_tests',
                         suffix='_failing_test')

  # Periodic scheduler triggered builds also don't contain revision.
  mainname = 'chromium.webrtc.fyi'
  yield generate_builder(mainname, 'Win Builder',
                         suffix='_periodic_triggered')

  # Testers gets got_revision value from builder passed as parent_got_revision.
  yield generate_builder(mainname, 'Win7 Tester',
                         suffix='_periodic_triggered')
  yield generate_builder(mainname, 'Android Tests (dbg) (L Nexus9)',
                         failing_test='content_browsertests',
                         suffix='_failing_test')
