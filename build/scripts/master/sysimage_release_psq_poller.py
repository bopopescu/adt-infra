# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This SysimageReleasePsqPoller polls system image release testing requests.

Each polled request triggers a series of tests on system images.

Notice that the gsutil configuration (.boto file) must be setup in either the
default location (home dir) or by using the environment variables
AWS_CREDENTIAL_FILE and BOTO_CONFIG.
"""

import os
import subprocess

from twisted.internet import defer
from twisted.python import log

from buildbot.changes import base
from common.presubmit.constants import Constants
import gcs_oauth2_boto_plugin
import StringIO
from boto import boto
from twisted.python import log

BASE_DIR = os.path.abspath(os.path.join(
               os.path.dirname(__file__), os.pardir, os.pardir))
GSUTIL_DIR = os.path.join(BASE_DIR, 'third_party', 'gsutil')
GSUTIL = os.path.join(GSUTIL_DIR, 'gsutil')

BUILD_NUMBER = 'build_number'

class SysimageReleasePsqPoller(base.PollingChangeSource):
  """Poll a Google Storage URL for a release testing request and submit to change master."""

  compare_attrs = ['changeurl', 'pollInterval']

  # pylint runs this against the wrong buildbot version.
  # In buildbot 8.4 base.PollingChangeSource has no __init__
  # pylint: disable=W0231
  def __init__(self, name, gs_bucket, gs_path_list, pollInterval=5*60,
               project=None, branch=None, name_identifier='', category=None):
    """Initialize SysimageReleasePsqPoller.

    Args:
    gs_bucket: bucket name
    gs_path_list: list of GS URLs to watch for
    pollInterval: Time (in seconds) between queries for changes.
    name_identifier: If given, used to identify if a file is important
    category: Build category to trigger (optional).
    """
    self.name = name
    self.cachepath = self.name + '.cache'
    self.gs_bucket = gs_bucket
    self.gs_path_list = gs_path_list
    self.pollInterval = pollInterval
    self.category = category
    self.last_build = None
    self.project = project
    self.branch = branch
    self.name_identifier = name_identifier

    if os.path.exists(self.cachepath):
      try:
        with open(self.cachepath, "r") as f:
          self.last_build = int(f.readline().strip())
          log.msg("%s: Setting last_build to %s" % (self.name, self.last_build))
      except:
        self.cachepath = None
        log.msg("%s: Cache file corrupt or unwriteable; skipping and not using" % self.name)
        log.err()

  def describe(self):
    return '%s: watching %s' % (self.name, self.gs_path_list)

  def poll(self):
    log.msg('%s: polling %s' % (self.name, self.gs_path_list))
    d = defer.succeed(None)
    d.addCallback(self.find_latest_request)
    d.addCallback(self._process_changes)
    d.addErrback(self._finished_failure)
    return d

  def _finished_failure(self, res):
    log.msg('%s: poll failed: %s. URL: %s' % (self.name, res, self.gs_path_list))

  def find_latest_request(self, _no_use):
    bucket = boto.storage_uri(self.gs_bucket, 'gs').get_bucket()
    build_number = None
    for obj in bucket.list(self.gs_path_list[0]):
      if self.name_identifier in obj.name:
        # request file path: "builds/[build_number]/test_config"
        build_number = max(build_number, int(obj.name.split('/')[1]))
    log.msg('%s: last_build %s, new_last_build %s' % (self.name, self.last_build, build_number))
    if build_number == None or build_number <= self.last_build:
      return None
    file_list = []
    for path in self.gs_path_list:
      objs = bucket.list(path + '%s/' % build_number)
      configs = [obj for obj in objs if self.name_identifier in obj.name]
      count = len(list(configs))
      log.msg("%s: search %s%s, configs count %s" % (self.name, path, build_number, count))
      if count != 1:
        log.msg("%s: there must be exactly one config in %s%s (actual count %s)" % (self.name, path, build_number, count))
        return None
      # download and parse the release test request file
      gs_full_path = 'gs://' + self.gs_bucket + '/' + configs[0].name
      proc = subprocess.Popen(['python', GSUTIL, 'cat', gs_full_path], stdout=subprocess.PIPE)
      output = proc.communicate()[0]
      print output
      lines = output.strip().split('\n')
      change_id = lines[0]
      change_revision = lines[1]
      for line in lines[2:]:
        file_list.append(line)
    return {Constants.CHANGE_ID: change_id,
            Constants.CHANGE_REVISION: change_revision,
            Constants.CHANGE_FILES: file_list,
            BUILD_NUMBER: build_number}

  def _update_last_build(self, new_build):
    log.msg("%s: last build changed from %s to %s" % (self.name, self.last_build, new_build))
    self.last_build = new_build
    if self.cachepath:
      with open(self.cachepath, "w") as f:
          f.write("%s\n" % self.last_build)

  def _process_changes(self, change):
    if change is None:
      return
    file_list = change[Constants.CHANGE_FILES]
    build_number = change[BUILD_NUMBER]
    if file_list is not None:
      self._update_last_build(build_number)
      props={Constants.CHANGE_FILES: ','.join(file_list),
             Constants.CHANGE_ID: change[Constants.CHANGE_ID],
             Constants.CHANGE_REVISION: change[Constants.CHANGE_REVISION]}
      self.master.addChange(who=self.name,
                            revision=build_number,
                            files=file_list,
                            project=self.project,
                            branch=self.branch,
                            comments='comment',
                            properties=props,
                            category=self.category)
