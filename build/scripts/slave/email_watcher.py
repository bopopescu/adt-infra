#!/usr/bin/python
"""Provides an email build status monitor which can be used as a decorator
around any recipe's RunSteps(api) method:

@EmailRecipeWatcher()
def RunSteps(api):
  # ...

Any exception thrown from RunSteps will be included into the report email.
However, in case of an email formatting/sending failure, the decorator itself
will not raise any exceptions in order to preserve the normal build
processing control flow. It will just log the corresponding message so that it
was easy to see what happened on the dashboard.

The decorator will not in any way impact the communication between the recipe
code and recipe API. It must be entirely transparent in this regard. This is
the main reason why email sending is not a separate step (the other one is
that email should capture all the steps, and should not really depend on the
underlying steps status
"""

import os
import datetime
import smtplib
import traceback
import sys

from urlparse import urljoin

from recipe_engine import recipe_api

# We use the default public smtp.gmail.com host for off-corp email
# This uses default port 25, which works with TLS/SSL
DEFAULT_SMTP_HOST = 'smtp.gmail.com'
# adtinfrastructure@gmail.com is the default chromeos lab gmail account
DEFAULT_SENDER = 'adtinfrastructure@gmail.com'
# The below addresses are what legacy 'master_mail_notifications' used.
DEFAULT_RECIPIENTS = ['adtinfrastructure@gmail.com']

# The below is a addition made from the base email_watchers.py file located in the studio-infra
# codebase.  This variable is required here as we are emailing from a outside gmail account
# (adtinfrastructure) and we need to properly form its login credentials, which are stored in
# a file within the below directory.
BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                                         os.pardir)

# Google Rotations maintain an email alias for each rotation, such that any
# email sent to that alias will end up in the current sheriff's inbox and
# associated group in CC. Hence specify the rotation aliases here to be able to
# send reports to the build sheriffs without actually having to know who they
# are exactly. The aliases are configurable in the rotation settings accesible
# via https://rotation.googleplex.com/
SHERIFF_ALIASES = [
  "emu-build-police-pst@grotations.appspotmail.com"
]

# Main tag to be included into each build email subject in order to
# simplify search / filtering
BUILD_EMAIL_TAG = "[adt_emu_buildbot_report]"

DEFAULT_DASHBOARD_LINK = "http://go/adt-builder"
# Set this to None if override of 'buildbotURL' supplied in API properties is
# not required. As of Aug 2016, it is preferable to have it for Studio
# use-case since buildbotURL directly points to the physical hostname running
# the dashboard, which is behind uberproxy and thus it makes browsing
# there a little bit annoying due to long response times. The override below is
# much friendlier as a base URL
OVERRIDE_BUILDBOT_URL = None

# Tree closers are basically the builder names we expect the sheriffs to
# monitor on a regular basis and take action if some of them fail.
# The tree closers list is defined by team policy and it is not expected that
# the corresponding recipe owners will disable the notifications in any way
# This doesnt apply directly to adt builder.  Leave this as empty string.
TREE_CLOSERS = [
  ""
]

# The sponge dashboard provides some good overview of specific tests history
# between the builds, so include it into the emails to make it easier to
# navigate directly to it
# Currently we do not pass SPONGE results for adt builder.  Leave these as empty strings.
SPONGE_URL_TEMPLATE = ""
SPONGE_AWARE_BUILDERS = [
  ""
]

# Make sure all the named parameters are properly elaborated in the format()
# call when the actual body is constructed
EMAIL_BODY_TEMPLATE = """
<html>
{blamelist_preamble}
{sheriff_preamble}
<b>Build result: {result}</b><br/>
<b>Reason:</b> {reason}<br/>
<b>Build duration:</b> {build_duration}<br/>
<br/>
<b>Builder:</b> {builder_name}<br/>
<b>Build number:</b> {build_number}<br/>
<b>Recipe:</b> {recipe_name}<br/>
<br/>
<b>Build slave used for this build:</b> {slave_name}<br/>
<br/>
See the full build results at {full_build_url}<br/>
<br/>
{sponge_info}<br/>
<br/>
<i>Properties dump:<br/><br/>{properties_dump}</i><br/>
<br/>
<i>Tag: {email_tag}</i><br/>
<br/>
<i>This report was generated at {report_time} UTC</i><br/>
</html>
"""

# Preambles to be included at the top of the email under certain circumstances
# to address specific people who are likely to take action following the report
BLAMELIST_PREAMBLE = """
<i>If you have been CC'ed into this email, it means that either some of your
recent CLs were included into this build, or your email address is mentioned
directly on the list of recipients specified in the recipe implementation.
If the former, it does not necessarily mean that your CL was the cause for its
breakage, however if you are aware of this builder and if your change might
have affected the build status, please respond to this email with the
information you have to offer. Thank you.<br/><br/></i>"""

SHERIFF_PREAMBLE = """
<i>If you are included directly into the 'To' list of recipients of this email,
it means you are the identified as the build sheriff today. Please take the
corresponding action to address the build failure. See more details
on sheriffing process and sheriffing calendar at go/studio-sheriff.<br/><br/>
If you believe this email is received by mistake or that the sheriff calendar
should be amended, please talk to android-devtools-team@ or make the changes
in the calendar yourself once the swap with someone on the team
has been agreed. Thank you.<br/><br/></i>
"""

# This is to log the email being sent to the output console
LOG_EMAIL_TEMPLATE = """
Build status email sent successfully with the following parameters:
From: {send_from}
To: {send_to}
Cc: {send_cc}
Subject: {email_subject}
Body:
{email_body}
"""

def sendEmail(send_from, send_to, subject, text,
              send_cc=[], files=[], smtp_host=DEFAULT_SMTP_HOST, tls_tuple=(),
              is_html=True):
  # The email imports below are tricky due to the evident changes in module
  # structure between different Python versions, so the code inspection might
  # be false positive or false negative
  from email.MIMEMultipart import MIMEMultipart
  from email.MIMEBase import MIMEBase
  from email.MIMEText import MIMEText
  from email.utils import COMMASPACE, formatdate
  from email import Encoders

  # If you really want to test this locally during simulations or by a plain
  # run of this file, uncomment the below and change accordingly.
  # Can use an application-specific password to be 100% sure the real one won't
  # leak somehow.
  # Local testing with the production settings is unlikely to succeed due to
  # SMTP relay policies.
  # In case of running this file directly without the simulation engine,
  # you might want to comment out all the references to recipe_api.* temporarily
  #tls_tuple = ("adehtiarov@google.com", "dwyesevsqoqqawwd")
  #smtp_host = "smtp.gmail.com:587"
  #send_from = "adehtiarov@google.com"
  #send_to = ["adehtiarov@google.com"]

  msg = MIMEMultipart('mixed')
  msg['From'] = send_from
  msg['To'] = COMMASPACE.join(send_to)
  msg['Date'] = formatdate(localtime=False, usegmt=True)
  msg['Subject'] = subject

  if send_cc:
    msg['Cc'] = COMMASPACE.join(send_cc)

  if text:
    msg.attach(MIMEText(text, 'html' if is_html else 'plain'))

  for f in files:
    if not f:
      continue
    part = MIMEBase('application', 'octet-stream')
    with open(f, 'rb') as fp:
      part.set_payload(fp.read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(f))
    msg.attach(part)

  smtp = smtplib.SMTP(smtp_host)
  if tls_tuple:
    smtp.starttls()
    smtp.login(*tls_tuple)

  # Need to specify all the recipients here, so join all the lists
  # The headers above will do the job in actually separating them
  all_recipients = send_to + send_cc
  smtp.sendmail(send_from, all_recipients, msg.as_string())
  smtp.quit()


class EmailRecipeWatcher:
  """
  To be used as a parametrized decorator for RunSteps(api)
  """
  def __init__(self, send_from=DEFAULT_SENDER, send_to=DEFAULT_RECIPIENTS,
               send_cc=[], cc_blamelist=True,
               smtp_host=DEFAULT_SMTP_HOST,
               tree_closers=TREE_CLOSERS):
    self.send_from = send_from
    self.send_to = send_to
    self.send_cc = send_cc
    self.smtp_host = smtp_host
    self.cc_blamelist = cc_blamelist
    self.tree_closers = tree_closers

  def _format_recipe_exception_reason(self, e):
    # The __str__ method implementations of the recipe API exceptions are
    # a bit clunky, so need to do some proper formatting here

    # WARNING: Be careful when modifying this function! As of writing it,
    # this function is only called in a context which is extremely sensitive to
    # any uncaught exceptions. So if it appears to throw,
    # things may get really wrong in the calling code and the whole email
    # sending logic
    if isinstance(e, recipe_api.InfraFailure):
      reason_type = "Infrastructure failure"
    elif isinstance(e, recipe_api.StepFailure):
      reason_type = "Step failure"
    else:
      return str(e)

    if hasattr(e, "name") and hasattr(e, "reason") and e.name:
      return "%s in %s: %s" % (reason_type, e.name, e.reason)
    elif hasattr(e, "reason"):
      return "%s: %s" % (reason_type, e.reason)

    return str(e)

  def __call__(self, RunSteps):
    def watched_RunSteps(api):
      # Don't wrap if this is a local run
      if (hasattr(api, "is_local_run") and
          hasattr(api.is_local_run, "__call__") and
          api.is_local_run()):
        return RunSteps(api)

      start_time = datetime.datetime.now()

      ret = None
      try:
        ret = RunSteps(api)
      except (recipe_api.InfraFailure, recipe_api.StepFailure) as e:
        result = "FAILED"
        reason = self._format_recipe_exception_reason(e)
        traceback.print_exc()
        # Vitally important to re-raise any exception as is,
        # otherwise build statuses may get screwed
        raise
      except Exception, e:
        result = "FAILED"
        reason = "Unexpected Python exception: %s" % e
        traceback.print_exc()
        # Vitally important to re-raise any exception as is,
        # otherwise build statuses may get screwed
        raise
      else:
        result = "OK"
        reason = "Build completed successfully"
      finally:
        # We need to store the active exception information (if any) in order
        # to 100% transparently re-raise it once email operation is complete.
        # The thing is that if email processing code throws another exception
        # (even though it's handled), it will overwrite the active exception
        # information potentially thrown earlier from the recipe,
        # and we'd never be able to re-raise it
        exc_type, exc_value, exc_tb = sys.exc_info()
        try:
          end_time = datetime.datetime.now()
          build_duration = str(end_time - start_time)

          direct_recipients = self.construct_direct_recipients(api, result)
          send_cc = self.construct_cc_recipients(api, result)
          email_body = self.construct_email_body(api, result, reason,
                                                 build_duration)
          email_subject = self.construct_email_subject(api, result, reason)

          if not 'TESTING' in api.properties: # pragma: no cover
            tls_username = DEFAULT_SENDER
            tls_password = ""
            try:
              with open(os.path.join(BUILD_DIR, 'site_config', '.mail_password')) as f:
                tls_password = f.read()
            except Exception as ex:
              print ("Failed to read password file. Exception: ", str(ex))
            tls_tuple = (tls_username, tls_password)
            sendEmail(self.send_from, direct_recipients, email_subject,
                      email_body, send_cc=send_cc, tls_tuple=tls_tuple)
            print LOG_EMAIL_TEMPLATE.format(
              send_from=self.send_from,
              send_to=direct_recipients,
              send_cc=send_cc,
              email_body=email_body,
              email_subject=email_subject)
        except Exception:
          print ("Failed to send build status email due to an exception: %s"
                 % traceback.format_exc())
          print "Properties dump: %s" % api.properties.thaw()

        if exc_value is not None:
          raise exc_type, exc_value, exc_tb

      return ret

    return watched_RunSteps

  def construct_direct_recipients(self, api, result):
    builder_name = api.properties.get('buildername')
    if result != "OK" and builder_name in self.tree_closers:
      direct_recipients = SHERIFF_ALIASES + self.send_to
    else:
      direct_recipients = self.send_to

    return direct_recipients

  def construct_cc_recipients(self, api, result):
    send_cc = self.send_cc
    if result != "OK" and self.cc_blamelist:
      # Do some preprocessing as we don't want anything to be sent
      # outside of @google.com. Non-google addresses can appear on the
      # blamelist when importing a git repository with history,
      # for example, and we have done that a couple of times already
      # Of course, a more sophisticated per-group check could be done
      # here, but domain restriction is good enough already.
      blamelist = filter(lambda a: a.lower().endswith('@google.com'),
                         api.properties.get('blamelist', []))
      send_cc += blamelist

    return send_cc

  def construct_email_body(self, api, result, reason, build_duration):
    # Typical populated properties set in the API object is below.
    # Revise from time to time to see what can be used in the email directly
    #
    # {u'workdir': u'/usr/local/google/home/studio-infra/adt_infra_internal/build/slave/studio_master-dev',
    # u'repository': u'https://googleplex-android.googlesource.com/platform',
    # u'buildername': u'studio_master-dev',
    # u'recipe': 'studio/studio',
    # u'mastername': u'client.studio',
    # u'manifest_branch': u'studio-master-dev',
    # u'scheduler': u'studio_post_commit_scheduler',
    # u'manifest_url': u'https://googleplex-android.googlesource.com/platform/manifest',
    # u'buildbotURL': u'http://wpie20.hot.corp.google.com:8200/',
    # u'project': u'all repo projects',
    # u'buildnumber': 4020,
    # u'slavename': u'studiobot1.eem.corp.google.com',
    # u'blamelist': [u'gavra@google.com'],
    # u'branch': u'studio-master-dev',
    # u'requestedAt': 1472122227,
    # u'revision': u'becfafa68c2b26c26eaed84555bb8286780693a1'}

    builder_name = api.properties.get('buildername')

    sheriff_preamble = ""
    blamelist_preamble = ""
    if result == "OK":
      result = "<font color='green'>OK</font>"
    else:
      result = "<font color='red'>%s</font>" % result
      blamelist_preamble = BLAMELIST_PREAMBLE
      if builder_name in self.tree_closers:
        sheriff_preamble = SHERIFF_PREAMBLE

    builder_name = api.properties.get('buildername')
    if builder_name in SPONGE_AWARE_BUILDERS:
      sponge_info = """This build is marked as integrated with sponge, so the
    detailed test execution history should also be available here: %s""" % (
        SPONGE_URL_TEMPLATE.format(builder_name=builder_name))
    else:
      sponge_info = ""

    body = EMAIL_BODY_TEMPLATE.format(
      result=result,
      reason=reason,
      build_duration=build_duration,
      builder_name=builder_name,
      build_number=api.properties.get('buildnumber'),
      recipe_name=api.properties.get('recipe'),
      slave_name=api.properties.get('slavename'),
      full_build_url=self.construct_full_build_url(api),
      properties_dump=api.properties.thaw(),
      report_time=str(datetime.datetime.utcnow()),
      sponge_info=sponge_info,
      blamelist_preamble=blamelist_preamble,
      sheriff_preamble=sheriff_preamble,
      email_tag=BUILD_EMAIL_TAG
    )
    return body

  def construct_full_build_url(self, api):
    # A typical full build URL:
    # https://android-jenkins.corp.google.com/builders/studio_master-dev/builds/4020
    if OVERRIDE_BUILDBOT_URL:
      base_url = OVERRIDE_BUILDBOT_URL
    else:
      base_url = api.properties.get('buildbotURL')
      if not base_url:
        return DEFAULT_DASHBOARD_LINK

    # To be appended to the base URL
    url_template = "builders/{builder_name}/builds/{build_number}"
    builder_name = api.properties.get('buildername')
    build_number = api.properties.get('buildnumber')
    if not build_number or not builder_name:
      return base_url

    full_url = urljoin(base_url,
                       url_template.format(builder_name=builder_name,
                                           build_number=build_number))
    return full_url

  def construct_email_subject(self, api, result, reason):
    # Populate with tags so that people could easily adjust their filters
    # per builder name
    builder_name = api.properties.get('buildername', '<unknown>')
    build_number = api.properties.get('buildnumber', '<unknown>')

    subj_template = "[{builder_name}] Build #{build_number}: {result}"
    subj = subj_template.format(builder_name=builder_name,
                                build_number=build_number,
                                result=result)

    return subj

if __name__ == "__main__":
  # Aiming to test the watcher end-to-end, employ the decorator pattern here in
  # the same way it will be used on real RunSteps(api) in the recipes
  @EmailRecipeWatcher()
  def RunSteps(api):
    print "Well, we are doing something in the recipe now..."
    import time
    time.sleep(3)

  # Simple stub for the real recipe API objects. All we need is the properties
  # dictionary, as far as this email watcher is concerned. Mimic PropertiesApi
  # interface as well, since it's not a plain dict under the hood
  class PropertiesApi:
    def __init__(self, vanilla):
      self.vanilla = vanilla

    def thaw(self):
      return self.vanilla

    def get(self, k, d=None):
      return self.vanilla.get(k, d)

    def __iter__(self):
      return iter(self.vanilla)

    def __len__(self):
      return len(self.vanilla)

  class TestApi:
    properties = PropertiesApi({
      'buildername': 'optimus-prime_master-dev',
      'buildnumber': 9000,
      'recipe': 'lorem/ipsum',
      'slavename': 'gear-4218902.big-corporation.com',
      'blamelist': [u'adehtiarov@google.com', u'droid@android.com',
                    u'opensource@example.com', u'etranger@google.com']
    })

  api = TestApi()

  # Press the big red button, see the output, adjust as appropriate
  RunSteps(api)

  # ...and the same for the failure use case
  # Test the failure report sending to sheriffs
  test_tree_closers = TREE_CLOSERS + [api.properties.get('buildername')]
  @EmailRecipeWatcher(tree_closers=test_tree_closers)
  def RunSteps_failure(api):
    print "We are doing something in the recipe but it will cease soon..."
    raise Exception(
      "Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, "
      "consectetur, adipisci velit...")

  try:
    # Let's test the sponge-aware case now
    SPONGE_AWARE_BUILDERS.append(api.properties.get('buildername'))
    RunSteps_failure(api)
  except Exception:
    print ("The following exception was propagated - make sure it is the "
           "intended one: %s" % traceback.format_exc())
  else:
    print ("No exception propagated when RunSteps() fails - this must NOT be "
           "the case, since the watcher is expected to have no impact on the "
           "control flow between recipe code and recipe engine!")
