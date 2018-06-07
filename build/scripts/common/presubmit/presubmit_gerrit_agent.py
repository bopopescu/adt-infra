class PresubmitGerritAgent:
  """
  Abstract class defining methods to communicate with Gerrit REST API.
  """

  def __init__(self, agent_lib):
    """
    @param agent_lib: AgentLib obj, contains all informations (Gerrit base URL, cookie jar, project name, branch name).
    @return:
    """
    self.agent_lib = agent_lib


  def get_pending_verifiables(self, since = 0):
    """
    Retrieve all Verifiable currently staged on Gerrit (since==0) or updated and ready for presubmit since |since|.
    @param since: datetime.
    @return: [IVerifiable]
    """
    raise Exception("Abstract class method called.")


  def verify(self, verifiable, verified_label, message):
    """
    Sends a SetReview request to Gerrit. Update change with "Verified:" label and "Message".
    @param verifiable: IVerifiable, containing the main_change to update.
    @param verified_label: str, new value of "Verified" label.
    @param message: str, message describing the reason of the Verifiable label update.
    @return: REST json response from Gerrit.
    """
    raise Exception("Abstract class method called.")