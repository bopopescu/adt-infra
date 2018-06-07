import apiclient
import httplib2
import oauth2client.client
import os
import pprint

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


def generate_git_information(poller):
  '''Return the proper git branch and target for the input.

  Args:
    poller:  The poller that found the change (example: 'sys_image_mnc_poller').

  Returns:
    The git branch and git target for the passed in poller to query AB with.
  '''
  if 'emulator_linux_poller' in poller or 'emulator_windows_poller' in poller:
    return 'aosp-emu-master-dev', 'sdk_tools_linux'
  elif 'emulator_mac_poller' in poller:
    return 'aosp-emu-master-dev', 'sdk_tools_mac'
  elif 'sys_image_mnc_poller' in poller:
    return 'git_mnc-emu-dev', 'sdk_google_phone_x86-sdk_addon'
  elif 'sys_image_gb_poller' in poller:
    return 'git_gb-emu-dev', 'sdk_x86-sdk'
  elif 'sys_image_ics-mr1_poller' in poller:
    return 'git_ics-mr1-emu-dev', 'sdk_x86-sdk'
  elif 'sys_image_jb_poller' in poller:
    return 'git_jb-emu-dev', 'sdk_x86-sdk'
  elif 'sys_image_jb-mr1.1_poller' in poller:
    return 'git_jb-mr1.1-emu-dev', 'sdk_x86-sdk'
  elif 'sys_image_jb-mr2_poller' in poller:
    return 'git_jb-mr2-emu-dev', 'sdk_x86-sdk'
  elif 'sys_image_lmp_mr1_poller' in poller:
    return 'git_lmp-mr1-emu-dev', 'sdk_google_phone_x86-sdk_addon'
  elif 'sys_image_nyc_dev_poller' in poller:
    return 'git_nyc-emu-dev', 'sdk_google_phone_x86-sdk_addon'
  elif 'sys_image_oc_mr1_car_support_release_poller' in poller:
    return 'git_oc-mr1-car-support-release', 'gcar_emu_x86-sdk_addon'
  elif 'sys_image_oc_dev_poller' in poller:
    return 'git_oc-emu-dev', 'sdk_gphone_x86-sdk_addon'
  elif 'sys_image_oc_mr1_dev_poller' in poller:
    return 'git_oc-mr1-emu-dev', 'sdk_gphone_x86-sdk_addon'
  elif 'sys_image_nyc_mr1_dev_poller' in poller:
    return 'git_nyc-mr1-emu-dev', 'sdk_google_phone_x86-sdk_addon'
  elif 'sys_image_klp_poller' in poller:
    return 'git_klp-emu-dev', 'google_sdk_x86-sdk_addon'
  elif 'sys_image_lmp_poller' in poller:
    return 'git_lmp-emu-dev', 'sdk_google_phone_x86-sdk_addon'
  elif 'sys_image_pi_dev_poller' in poller:
    return 'git_pi-dev', 'sdk_gphone_x86-sdk_addon'
  elif 'sys_image_pi_car_dev_poller' in poller:
    return 'git_pi-car-dev', 'aosp_car_x86_64-userdebug'
  elif 'sys_image_master_poller' in poller:
    return 'git_master', 'sdk_gphone_x86-sdk_addon'
  elif 'sys_image_aosp_poller' in poller:
    return 'aosp-master', 'sdk_x86-sdk'
  elif 'emulator_2.7_linux_poller' in poller or 'emulator_2.7_windows_poller' in poller:
    return 'aosp-emu-2.7-release', 'sdk_tools_linux'
  elif 'emulator_2.7_mac_poller' in poller:
    return 'aosp-emu-2.7-release', 'sdk_tools_mac'
  else:
    raise NotImplementedError('The passed in poller: %s, does not have a '
                              'implementation.' % (poller))


def query_ab(poller, prevRevision, currRevision):
  '''Entry function for master from gs_multi_poller.py to create changes.

  Args:
    poller: The poller (such as 'emulator_linux_poller') that initiated the change.
    prevRevision: The previous revision (last built revision) for this poller.
    currRevision: The current revision (that triggered poller) for this poller.

  Returns:
    A python list of all of the changes associated with this build (all changes
    between the prevRevision (exclusive) and the currRevision (inclusive).
  '''
  git_branch, git_target = generate_git_information(poller)
  creds = LoadCredentials()
  ab_client = getApiClient(creds)
  req = ab_client.build().list(branch=git_branch,
                               buildType='submitted',
                               target=git_target,
                               startBuildId=currRevision,
                               endBuildId=prevRevision,
                               extraFields='changeInfo')
  resp = req.execute()
  if 'builds' not in resp:
    raise ValueError('Failed to retrieve data from AndroidBuild API')
  changeSets = []
  for build in resp['builds']:
    for changes in build['changes']:
      if 'changeNumber' not in changes:  # We sometimes get merged changes with no actual number.  Ignore them.
        continue
      changeSet = {}
      changeSet['buildId']      = build['buildId']
      changeSet['email']        = changes['revisions'][0]['commit']['author']['email']
      changeSet['changeNumber'] = changes['changeNumber']
      changeSet['subject']      = changes['revisions'][0]['commit']['subject']
      changeSet['branch']       = changes['branch']
      changeSets.append(changeSet)
  return changeSets

if __name__ == '__main__':
  creds     = LoadCredentials()
  ab_client = getApiClient(creds)
  req = ab_client.build().list(branch='aosp-emu-master-dev',
                               buildType='submitted',
                               target='sdk_tools_linux',
                               startBuildId=3578761,
                               endBuildId=3566000,
                               extraFields='changeInfo')
  resp = req.execute()
  pprint.pprint(resp)
