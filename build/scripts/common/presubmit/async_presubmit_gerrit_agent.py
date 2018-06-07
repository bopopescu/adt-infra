from presubmit_gerrit_agent import PresubmitGerritAgent
from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred
from twisted.python import log
from twisted.internet import defer
from zope.interface import implements

from change import Change
from topic import Topic

import json
import os


class ASyncPresubmitGerritAgent(PresubmitGerritAgent):
  """
  Gerrit agent based on Twisted Deferred callbacks.

  """

  class BeginningPrinter(Protocol):
    """
    Asynchronously read data as it is received. Stored it all in |self.data|, fire Deferred once connection is
    closed/lost.
    """
    def __init__(self, finished):
        """
        @param finished: Deferred object.
        """
        self.data = ""
        self.finished = finished

    def dataReceived(self, bytes):
       """
       Aggregate data received in a private buffer.
       """
       self.data += bytes

    def connectionLost(self, reason):
        self.finished.callback(self.data)

  class BodyProducer():
    implements(IBodyProducer)

    def __init__(self, json_object):
      self.body_string = json.dumps(json_object)
      self.length = len(self.body_string)

    def startProducing(self, consumer):
      consumer.write(self.body_string)
      return succeed(None)

    def stopProducing(self):
      pass

    def pauseProducing(self):
      pass

  def __init__(self,agent_lib):
    """
    @param agent_lib: AgenList object.
    """
    PresubmitGerritAgent.__init__(self, agent_lib)

  def parse_topic_json(self, json_string, topic):
    """
    Parses json (array of Changes) and return a Topic.
    @param json_string: str, json representation of all changes for a topic.
    @param topic: Change obj, the "main change" of this topic.
    @return: Topic.
    """
    print "START_JSON_TOPIC: %s" % topic
    try:
      print json_string
    except:
      print 'Error printing json_string for topic: %s' % topic
    print "END_JSON_TOPIC: %s" % topic
    try:
      changes = Change.parseJson(json_string)
      main_change_number = topic.number
      changes = [x for x in changes if x.number != main_change_number]
      return Topic(topic, changes)
    except Exception as e:
      print 'Exception: Did not add topic "%s". See info below:' % topic
      print e
      return None

  def parse_changes_json(self, json_string):
    """
    Parses json (array of Changes) and return an array of Verifiable.

    If a verifiable has supporting changes, those are also retrieved from Gerrit (one query per main change).
    @param json_string: str
    @return: [Verifiable]
    """
    print "START_JSON_CHANGES"
    try:
      print json_string
    except:
      print 'Error printing json_string from query.'
    print "END_JSON_CHANGES"

    changes = Change.parseJson(json_string)

    # Discard changes we deem invalid. Ideally we would filter out Changes at the Gerrit query
    # level but the query language doesn't allow it.
    simple_changes = [x for x in changes if self.agent_lib.is_valid(x) and not x.is_topic()]
    topics = [x for x in changes if self.agent_lib.is_valid(x) and x.is_topic()]

    deferrers = []
    for change in simple_changes:
      d = defer.Deferred()
      d.addCallback(lambda x: x)
      reactor.callWhenRunning(d.callback, change)
      deferrers.append(d)

    for change in topics:
      q = defer.Deferred()
      q.addCallback(self.retrieve_topic)
      reactor.callWhenRunning(q.callback, change)
      deferrers.append(q)

    print "{0} deferrers".format(len(deferrers))
    gatherer = defer.gatherResults(deferrers)
    return gatherer


  def get_cookie_headers(self, url):
    """
    Builds a list of entries which should be included in the "Cookie:" HTTP headers when opening a connection
    with |url|.

    @param url: str
    @return: [str]
    """
    cookies_headers = []
    cookies = self.agent_lib.get_cookies_for_url(url)
    for key,value in cookies.items():
      cookies_headers.append("{0}={1}".format(key, value))
    return cookies_headers

  def fake_retrieve_topic(self, change):
    """
    Mocked retrieve_topic function hitting HDD instead of the network.
    @param change: Change object.
    @return: Topic object
    """
    path = os.path.dirname(__file__)
    path += "/../presubmit_test/data/gerrit_reply_topic.json"
    f = open(path)
    c = f.read()
    f.close()
    topic = self.parse_topic_json(c, change)
    return topic

  def retrieve_topic(self, change):
    """
    Retrieves all changes related to a topic string.

    @param change: Change
    @return: Topic
    """
    agent = Agent(reactor)
    url = self.agent_lib.get_query_for_topic(change)
    log.msg("Sending GET to '{0}'.".format(url))
    cookies_headers = self.get_cookie_headers(url)
    d = agent.request('GET', url, Headers({"Cookie": cookies_headers}), None)

    def cbResponse(response):
      finished = Deferred()
      response.deliverBody(self.BeginningPrinter(finished))
      return finished

    d.addCallback(cbResponse)
    d.addCallback(self.parse_topic_json, change)
    return d

  def fake_get_verifiables(self, since=0):
    """
    Mocked version of get_verifiables which hit HDD instead of the network.
    @param since:
    @return:
    """
    path = os.path.dirname(__file__)
    path += "/../presubmit_test/data/gerrit_reply_multi_changes.json"
    f = open(path)
    c = f.read()
    f.close()
    changes = Change.parseJson(c)

    # Last change is a topic.
    topic = changes.pop()
    changes.append(self.fake_retrieve_topic(topic))

    d = Deferred()
    d.addCallback(lambda x: changes)
    reactor.callWhenRunning(d.callback, None)
    return d

  def verify(self, change_id, change_revision, verified_label, message):
    """

    @param change_id:
    @param change_revison:
    @param verified_label:
    @param message:
    @return:
    """
    agent = Agent(reactor)
    url = self.agent_lib.get_query_to_verify(change_id, change_revision)
    if verified_label is "0":
      json_object = {"message": message}
    else:
      json_object = {"message": message, "labels": {"Verified": verified_label}}

    print 'async verify url:'
    print url
    body = self.BodyProducer(json_object)
    cookies_headers = self.get_cookie_headers(url)
    d = agent.request('POST', url, Headers({"Cookie": cookies_headers, "Content-Type": ["application/json"]}), body)

    def cbResponse(response):
      finished = Deferred()
      response.deliverBody(self.BeginningPrinter(finished))
      return finished

    d.addCallback(cbResponse)
    return d

  def get_verifiables(self, since):
    """
    Retrieve all Changes and Topics ready to be reviewed and updated after |since|.
    @param since: datetime
    @return: [IVerifiable]
    """
    agent = Agent(reactor)
    url = self.agent_lib.get_query_for_verifiables(since)
    log.msg("Sending GET to '{0}'.".format(url))
    cookies_headers = self.get_cookie_headers(url)
    d = agent.request('GET', url, Headers({"Cookie": cookies_headers}), None)

    def cbResponse(response):
      finished = Deferred()
      response.deliverBody(self.BeginningPrinter(finished))
      return finished

    d.addCallback(cbResponse)
    d.addCallback(self.parse_changes_json)
    return d
