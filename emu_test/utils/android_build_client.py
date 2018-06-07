import apiclient
import httplib2
import oauth2client.client
import os

# Location of the credentials file for the android build API,
# relative to the User's Home Directory.
HOMEDIR_JSON_CREDENTIALS_PATH = '.ab_credentials.json'

# Scope URL on which we need authorization.
DEFAULT_SCOPE_URL = 'https://www.googleapis.com/auth/androidbuild.internal'

# Default Service name and version to connect to.
DEFAULT_API_SERVICE_NAME = 'androidbuildinternal'
DEFAULT_API_VERSION      = 'v2beta1'

def LoadCredentials(json_credentials_path=None, scope_url=None):
  '''Load the credentials from a local file.

  Returns a scoped credentials object which can be used to .authorize() a
  httlib2.Http() instance used by an apiclient.

  This method works with both service accounts (JSON generated from pantheon's
  API manager under Credentials section), or with authenticated users (using a
  scheme scimiliar to the one used by 'gcloud auth login'.)

  Args:
    json_credentials_path: Path to a JSON file with credentials for a service
      account or for authenticated user.  Defaults to looking for one using
      FindCredentialsFile().
    scope_url:  URL in which the credentials should be scoped.

  Returns:
    A scoped oauth2client.client.Credentials object that can be used to
    authorize an Http instance used by an apiclient object.
  '''
  if json_credentials_path is None:
    user_homedir = os.path.expanduser('~')
    if not user_homedir:
      raise Exception('Could not locate user home directory.')
    json_credentials_path = os.path.join(user_homedir, HOMEDIR_JSON_CREDENTIALS_PATH)
    if not os.path.exists(json_credentials_path):
      raise Exception('Could not find JSON credentials file at: %s' %
                      (json_credentials_path))
  # This is the way to support both service account credentials (JSON generated
  # from Pantheon) or authenticated users (similiar to 'gcloud auth login').
  google_creds = oauth2client.client.GoogleCredentials.from_stream(
      json_credentials_path)
  if scope_url is None:
    scope_url = DEFAULT_SCOPE_URL
  # We need to rescope the credentials which are currently unscoped.
  scoped_creds = google_creds.create_scoped(scope_url)
  return scoped_creds


def getApiClient(creds, api_service_name=None, api_version=None):
  '''Build an API client for androidbuild and authorize it.

  Args:
    creds: The scoped oauth2client.client.Credentials to use for authorization.
    api_service_name: Optional override for the API service name.
    api_version: Optional override for the API version.

  Returns:
    An apiclient.discovery.Resource that supports the androidbuild API methods.
  '''
  if api_service_name is None:
    api_service_name = DEFAULT_API_SERVICE_NAME
  if api_version is None:
    api_version      = DEFAULT_API_VERSION
  base_http_client = httplib2.Http()
  auth_http_client = creds.authorize(base_http_client)
  ab_client        = apiclient.discovery.build(api_service_name, api_version,
                                               http=auth_http_client)
  return ab_client
