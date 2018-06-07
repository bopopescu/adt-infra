import json

from StringIO import StringIO
from verifiable import IVerifiable

class Change(IVerifiable):
  """
  A change is a set of files stagged in Gerrit with metadatas.
  """

  def __init__(self, change_info, revision_info, fetch_info):
    self.revision_info = revision_info
    self.change_info = change_info
    self.fetch_info = fetch_info

  @staticmethod
  def parseJson(json_string):
    """
    Parses json representation of a set of Changes.
    @param json_string: str.
    @return: [Changes]
    """
    def encode_str(s):
      """Tries to encode a string into a python str type.
      Currently buildbot only supports ascii. If we have an error decoding the
      string (which means it might not be valid ascii), we decode the string with
      the 'replace' error mode, which replaces invalid characters with a suitable
      replacement character.
      """
      try:
        return str(s)
      except UnicodeEncodeError:
        return s.encode('utf-8', 'replace')
      except UnicodeDecodeError:
        return s.decode('utf-8', 'replace')

    changes = []
    json_string = encode_str(json_string)
    # Remove XSSI attack protection if there is one.
    if json_string.startswith(")]}'"):
      json_string = json_string[len(")]}'"):]
    io = StringIO(json_string)
    json_changes = json.load(io)
    for json_change in json_changes:
      try:
        change_info = json_change
        revision_info = change_info["revisions"][change_info["current_revision"]]
        fetch_info = revision_info["fetch"]["repo"]
        change = Change(change_info, revision_info, fetch_info)
        changes.append(change)
      except KeyError as e:
        print 'KeyError: Did not add change. See info below:'
        print e
        print json_change
    return changes

  def __str__(self):
    return self.change_info["id"] + " " + self.change_info["subject"]

  __repr__ = __str__


  def get_all_changes(self):
    """
    Implements abstract function defined in superclass.
    """
    return [self]


  def get_main_change(self):
    """
    Implements abstract function defined in superclass.
    """
    return self


  def is_topic(self):
    """
    Implements abstract function defined in superclass.
    """
    return "topic" in self.change_info and self.change_info["topic"]


  @property
  def number(self):
    """
    Syntactic sugar to access number property.
    """
    return self.change_info["_number"]
