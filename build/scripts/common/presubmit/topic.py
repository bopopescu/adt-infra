from verifiable import IVerifiable

class Topic(IVerifiable):
  """
  A Topic is a Change which needs other Changes to be valid. Example: A developer working on a feature involving
  a server and a client (both in different project/branch): His feature needs both of these changes to go in repo
  together in order for the feature to work.

  The main change is the original change (it can be any change with the same "topic' label)
  The "needed changes" (all other changes with the same "topic" label except main_change) are called
  "supporting changes".
  """

  def __init__(self, main_change, supporting_changes):
    self.main_change = main_change
    self.supporting_changes = supporting_changes

  def __str__(self):
    string = str(self.number) + "->("
    for change in self.supporting_changes:
      string += change.__str__() + ","
    string += ")"
    return string

  def detailed_string(self):
    string = "Topic (Project and Supporting Changes):\n\n"
    num_changes = 0

    string += "Main Change:\n"
    string += "============\n"
    string += " "
    string += self.main_change.__str__()
    string += "\n"

    string += "Supporting Changes:\n"
    string += "===================\n"
    for change in self.supporting_changes:
      string += str(num_changes)
      num_changes += 1
      string += ": "
      string += change.__str__()
      string += "\n"

    return string

  __repr__ = __str__


  def get_main_change(self):
    """
    Implements abstract function defined in superclass.
    """
    return self.main_change


  def get_all_changes(self):
    """
    Implements abstract function defined in superclass.
    """
    changes = self.supporting_changes[:]
    changes.append(self.main_change)
    return  changes

  def is_topic(self):
    """
    Implements abstract function defined in superclass.
    """
    return True

  @property
  def number(self):
    """
    Syntactic sugar to access number property.
    """
    return self.main_change.number

