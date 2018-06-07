from async_presubmit_gerrit_agent import ASyncPresubmitGerritAgent
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.defer import Deferred
from twisted.python import log


class ASyncGerritAgent(ASyncPresubmitGerritAgent):
  """
  Gerrit agent based on Twisted Deferred callbacks.

  This agent extends ASyncPresubmitGerritAgent. This agent overrides get_verifiables
  to not require presubmit-ready labels (e.g., code-review=+2) in query. It serves
  for a more general purpose.
  """

  def get_verifiables(self, since):
    """
    Retrieve all Changes and Topics ready to be reviewed and updated after |since|.
    @param since: datetime
    @return: [IVerifiable]
    """
    agent = Agent(reactor)
    url = self.agent_lib.get_query_for_verifiables(since, presubmit=False)
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
