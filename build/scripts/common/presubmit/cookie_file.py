from cookie import Cookie

class CookieFile:
  """
  Helper class to manipulate Cookie Jar files.
  """

  def __init__(self, file_path):
    self.cookies = []
    self.parse(file_path)


  def parse(self, filename):
    """
    Parses Netscape HTTP Cookie files. The format of a cookie file is described here:
    http://www.cookiecentral.com/faq/#3.5

    Content sample:
    # Netscape HTTP Cookie File
    # http://www.netscape.com/newsref/std/cookie_spec.html
    # This is a generated file!  Do not edit.
    #HttpOnly_login.corp.google.com FALSE/TRUE 1443186342 name value

    :param filename: The path where to find the cookie file.
    :return: None
    """
    with open(filename, "r") as file:
      for line in file:

        line = line.strip()

        # Skip empty line.
        if not line:
          continue

        # Skip comments.
        if line.startswith("# "):
          continue

        cookie = Cookie(line)
        self.cookies.append(cookie)


