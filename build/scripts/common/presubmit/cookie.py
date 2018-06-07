class Cookie:
  """
  Parses and stores all information found in a line of a Cookie file.
  Expected format:
  #(HttpOnly_)login.corp.google.com FALSE / TRUE    1443186342      name     value
  """

  HTTP_ONLY_PREFIX = "#HttpOnly_"

  def __init__(self, line):
    tokens = line.split("\t")

    if len(tokens) != 7:
      message = "Unable to parse cookie '{0}', found '{1}' tokens.".format(line).len(tokens)
      raise Exception(message)

    # Microsoft hack to implement httpOnly is to prefix a cookie line with
    # "#HttpOnly_". We need to remove it here.
    # https://www.owasp.org/index.php/HttpOnly
    self.http_only = tokens[0].startswith(self.HTTP_ONLY_PREFIX)
    self.domain = tokens[0].replace(self.HTTP_ONLY_PREFIX, "")
    self.sub_domain_available = ("TRUE" == tokens[1])
    self.path = tokens[2]
    self.secure_connection_required = "TRUE" == tokens[3]
    self.expiration_date = int(tokens[4])
    self.key = tokens[5]
    self.value = tokens[6]


