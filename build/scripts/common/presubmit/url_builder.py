import urllib


class UrlBuilder:
  """
  Helper class to build urls.

  Format used: base_url + path + 'q=" + searchTerms + "&" + parameters
  """

  def __init__(self):
    self.base_url = ""
    self.path = ""
    self.labels = []
    self.or_labels = []
    self.projects = []
    self.parameters = []


  def add_path(self, path):
    """
    Appends a path element to self.path.
    @param path: str
    """
    self.path += path


  def set_base_url(self, base_url):
    """
    Sets base_url.
    @param base_url: str
    """
    self.base_url = base_url


  def add_parameter(self, name, value):
    """
    Adds a parameter string to the url.

    @param name: str
    @param value: str
    """
    self.parameters.append((name,value))


  def add_project_search_term(self, project):
    """
    Adds a special project search terms for project
    @param project: string project name
    """
    self.projects.append(project)


  def add_search_term(self, name, value):
    """
    Adds a name:value in the q url parameter
    @param name: str
    @param value: str
    """
    self.labels.append((name,value))


  def add_or_search_terms(self, name_val_pairs):
    """
    Adds a series of name:value pairs +OR+'d together in the q url parameter
    @param (name, value) lst of labels and their values to be OR'd
    """
    self.or_labels.append(name_val_pairs)


  def build(self):
    """
    Joins all components together to form an url.
    @return: str, (url)
    """
    url = ""
    url += self.base_url
    url += self.path

    parameter_separator = "?"
    if len(self.labels):
      url += parameter_separator
      url += "q="
      url += self.build_labels_string()
      url += self.build_or_labels_string()
      if self.projects:
        url += "+" + self.build_projects_string()
      parameter_separator = "&"
      url += parameter_separator

    url += urllib.urlencode(self.parameters)
    return url


  def build_labels_string(self):
    """
    Builds a Gerrit REST query component (content of http parameter q value).
    @return: str
    """
    label_string = ""
    separator = ""
    for key, value in self.labels:
      label_string += separator
      label_string += urllib.quote_plus(key)
      label_string += ":"
      label_string += urllib.quote_plus(value)
      separator = "+"
    return label_string


  def build_or_labels_string(self):
    label_string = ""
    separator = ""
    for name_val_pairs in self.or_labels:
      label_string += "+("
      for key, value in name_val_pairs:
        label_string += separator
        label_string += urllib.quote_plus(key)
        label_string += ":"
        label_string += urllib.quote_plus(value)
        separator = "+OR+"
      label_string += ")"
      separator = ""
    return label_string


  def build_projects_string(self):
    """
    Builds the Gerrit REST query component containing the projects
    @return: str
    """
    label_string = "("
    separator = ""
    for project in self.projects:
      label_string += separator
      label_string += "project:%s" % project
      separator = "+OR+"
    label_string += ")"
    return label_string
