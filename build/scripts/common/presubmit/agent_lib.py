from cookie_file import CookieFile
from url_builder import UrlBuilder

import re
import urlparse

class AgentLib:
  """
  A set of functions used by both Gerrit agents (sync and async).
  """
  def __init__(self, base_url, cookie_filename, projects, branch, path):
    """

    @param base_url: str, format expected: "https://googleplex-android-review.git.corp.google.com", url to gerrit REST api.
    @param cookie_filename: str, format expected: "/a/b/.gitcookies", path to a nestscape cookie file.
    @param projects: [str], format expected: ["platform/tools/base", ...], project names to monitor
    @param branch: str, format expected: studio-main-dev, branch name to monitor
    @param path: str, format expected: regex, all files in change (C) MUST match the path to be a valid (C).
    @return:
    """
    self.base_url = base_url
    if base_url[-1] != '/':
       self.base_url += '/'
    self.cookies = CookieFile(cookie_filename).cookies
    self.projects = projects
    self.branch = branch
    self.path = path

  def get_query_for_verifiables(self, since=0, presubmit=True):
    """
    Builds an URL to query Gerrit REST service for changes ready to go in presubmit.
    Only retrieve changes for the lib current projects and change.

    @param since: str, datetime formatted to gerrit format. Only return changes updated after |since|.
    @param presubmit: bool, if the query requires presubmit-ready labels.
    @return: str, url encoded.
    """
    b = UrlBuilder()
    b.set_base_url(self.base_url)
    b.add_path("a/")
    b.add_path("changes/")
    b.add_search_term("status", "open")
    for project in self.projects:
      b.add_project_search_term(project)
    b.add_search_term("branch", self.branch)
    # We need to query for Presubmit-Verified=1 because TreeHugger may change
    # Presubmit-Ready+1 to Presubmit-Verified=1 before the PSQ poller polls.
    if presubmit:
      b.add_or_search_terms([("label", "Code-Review=1"),
                             ("label", "Code-Review=2"),
                             ("label", "Presubmit-Ready=1"),
                             ("label", "Presubmit-Verified=1")])
      b.add_search_term("-label", "Verified+1")
      b.add_search_term("-label", "Verified+2")
    if since:
      b.add_search_term("since", '"' + since + '"')
    b.add_parameter("o", "CURRENT_REVISION")
    b.add_parameter("o", "CURRENT_FILES")
    b.add_parameter("o", "DETAILED_ACCOUNTS")
    b.add_parameter("n", "100")
    b.add_parameter('o', 'MESSAGES')
    return b.build()

  def get_query_for_topic(self, change):
    """
    Builds an URL to query Gerrit REST service for all changes part of a change's topic.

    @param change: The "main change" (see Topic class for more details). of the topic
    @return: str, url encoded.
    """
    b = UrlBuilder()
    b.set_base_url(self.base_url)
    b.add_path("a/")
    b.add_path("changes/")
    b.add_search_term("status", "open")
    b.add_search_term("branch", self.branch)
    b.add_search_term("topic", change.change_info["topic"].encode('ascii','ignore'))
    b.add_parameter("o", "CURRENT_REVISION")
    b.add_parameter("o", "CURRENT_FILES")
    b.add_parameter("o", "DETAILED_ACCOUNTS")
    b.add_parameter("n", "100")
    return b.build()

  def get_query_to_verify(self, change_id, change_revision):
    """
    Builds an URL to query Gerrit REST service for all changes part of a change's topic.
    Details in SetReview (https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#set-review)

    @param change_id: str, The id of the change to update.
    @param change_revision: src, The current_revision of the change to update.
    @return: str, url encoded.
    """
    b = UrlBuilder()
    b.set_base_url(self.base_url)
    b.add_path("a/")
    b.add_path("changes/")
    b.add_path(change_id)
    b.add_path("/revisions/")
    b.add_path(change_revision)
    b.add_path("/review")
    return b.build()

  def is_valid(self, change):
    """
    Verifies a change is valid according to:
     - its uploader email (must a googler, ending in google.com).
     - the path of the files the change affects. All changes must match the |self.path| regex.

    @param change: Change object.
    @return: True is the change is valide.
    """
    revision = change.revision_info
    valid = True
    for file in revision["files"].keys():
      valid = (valid and re.match(self.path, file))

    if (not revision["uploader"] or not revision["uploader"]["email"].endswith("google.com")):
        valid = False

    return valid

  def get_cookies_for_url(self, url):
    """
    Builds a set of key/value which should be sent to a url via the "Cookie" header.

    @param url: str, the target url.
    @return: dict, name/values.
    """
    cookies = {}
    for cookie in self.cookies:
      o = urlparse.urlparse(url)
      if cookie.domain in o.hostname:
        if cookie.key not in cookies:
          cookies[cookie.key] = cookie.value
    return cookies
