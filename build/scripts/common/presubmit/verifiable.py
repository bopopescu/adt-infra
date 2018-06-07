class IVerifiable:
  """
  A verifiable can be either a single change or a set of change sharing the same topic field string.
  """

  def __init__(self):
    """

    @return:
    """
    raise Exception("Called Verifiable base method.")


  def get_changes(self):
    """

    @return:
    """
    raise Exception("Called Verifiable base method.")


  def get_main_change(self):
    """

    @return:
    """
    raise Exception("Called Verifiable base method.")

  def is_topic(self):
    """

    @return:
    """
    raise Exception("Called Verifiable base method.")