import urllib2
import urllib
import json

from change import Change
from topic import Topic
from presubmit_gerrit_agent import PresubmitGerritAgent

class SyncPresubmitGerritAgent(PresubmitGerritAgent):


  def __init__(self, agent_lib):
    PresubmitGerritAgent.__init__(self, agent_lib)


  def get_first_pending_verifiable(self):
    """

    @return:
    """
    verifiables = self.get_pending_verifiables()
    if not len(verifiables):
      return None
    return verifiables[-1]


  def get_pending_verifiables(self):
    """

    @return:
    """
    url = self.agent_lib.get_query_for_verifiables()
    s = self.request(url)
    changes = Change.parseJson(s)

    # Discard changes we deem invalid. Ideally we would filter out Changes at the Gerrit query
    # level but the query language doesn't allow it.
    simple_changes = [x for x in changes if self.agent_lib.is_valid(x) and not x.is_topic()]
    topics = [x for x in changes if self.agent_lib.is_valid(x) and x.is_topic()]

    # Check if any of the Changes are part of a Topic
    retrieved_topics = []
    for topic in topics:
      retrieved_topic = self.retrieve_topic(topic)
      retrieved_topics.append(retrieved_topic)

    verifiables = []
    verifiables.extend(simple_changes)
    verifiables.extend(retrieved_topics)
    return verifiables


  def retrieve_topic(self, topic):
    """

    @param change:
    @return:
    """
    url = self.agent_lib.get_query_for_topic(topic)
    s = self.request(url)
    changes = Change.parseJson(s)
    main_change_number = topic.number
    changes = [x for x in changes if x.number != main_change_number]
    return Topic(topic, changes)

  def verify(self, change_id, change_revision, verified_label, message):
    """

    @param change_id:
    @param change_revison:
    @param verified_label:
    @param message:
    @return:
    """
    url = self.agent_lib.get_query_to_verify(change_id, change_revision)
    if not verified_label or verified_label is "0":
      json_object = {"message": message}
    else:
      json_object = {"message": message, "labels": {"Verified": verified_label}}

    body = json.dumps(json_object)
    return self.request(url, body)


  def request(self, url, content = None):
    """

    @param url:
    @param content:
    @return:
    """
    req = urllib2.Request(url)

    if content:
      req.add_data(content)

    # For authentication purposes we need to add cookie values.
    headers = self.agent_lib.get_cookies_for_url(url)
    for key, value in headers.items():
      req.add_header("Cookie", "{0}={1}".format(key, value))

    req.add_header("Content-Type", "application/json")
    response = urllib2.urlopen(req)
    response_body = response.read()
    return response_body


