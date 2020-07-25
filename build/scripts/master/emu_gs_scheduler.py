# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This SingleBranchScheduler download necessary emulator package and include it in build properties

"""

import os, sys
import gcs_oauth2_boto_plugin
import StringIO
from boto import boto
from twisted.python import log
from twisted.internet import defer, utils
from buildbot.schedulers.timed import Periodic
from buildbot.schedulers.basic import SingleBranchScheduler

google_storage = 'gs'

class EmulatorSingleBranchScheduler(SingleBranchScheduler):
  """Augmented 'SingleBranchScheduler' that adds emu_image properties"""

  # Overrides 'SingleBranchScheduler.addBuildsetForChanges'
  @defer.inlineCallbacks
  def addBuildsetForChanges(self, *args, **kwargs):

    def addBuildset(change):
      if change['branch'] != "all":
        builders = [x for x in self.builderNames if change['branch'] in x]
      else:
        builders = self.builderNames
      if len(builders) == 0:
        log.msg("%s: no builder interested, skip this change" % self.name)
        return
      self.properties.setProperty('got_revision', change['revision'], 'Scheduler')
      self.properties.setProperty('logs_dir', os.path.join(os.getcwd(), 'subordinate_logs', ''), 'Scheduler')
      self.properties.setProperty(change['project'], change['revision'], 'Scheduler')
      kwargs['changeids'] = [change['changeid']]
      return SingleBranchScheduler.addBuildsetForChanges(
        self,
        builderNames=builders,
        *args,
        **kwargs)

    for cid in kwargs["changeids"]:
      try:
        d = self.main.db.changes.getChange(cid)
        d.addCallback(addBuildset)
        yield d
      except Exception as e:
        log.msg("Error adding build for change %s" % e)
        pass
