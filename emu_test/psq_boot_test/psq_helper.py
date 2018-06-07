import sys
import io
import shutil
import os
import zipfile
from emu_test.utils import android_build_client as abclient

# Location of emulator zip file download.
EMULATOR_ZIP_DOWNLOAD_DIR = '/tmp/'
RESOURCE_ID_BASE = 'sdk-repo-%s-emulator-%s.zip'


def getPlatform():
  """
  Wrapper function to return the current platform in the form that AB server
  is expecting.  'sys.platform' returns 'win32', however AB expects just 'win'.

  :return: Platform we are currently executing on.
  """
  if sys.platform is 'win32':
    return 'win'
  else:
    return 'linux'


def downloadArtifact(build_id, target, attempt_id='0'):
  """
  Download the artifact identified by build_id and target from the AB server.
  The file will be placed into 'EMULATOR_ZIP_DOWNLOAD_DIR/RESURCE_ID_BASE'

  :param build_id: The AB build_id for artifact.
  :param target: The AB target for artifact.
  :param attempt_id: Number of attempts to try.  0 means only once.

  :return: emu_filepath: Filepath to the emulator zip file.
  """
  creds = abclient.LoadCredentials()
  ab_client = abclient.getApiClient(creds)
  platform = getPlatform()
  resource_id = RESOURCE_ID_BASE % (platform, build_id)
  req = ab_client.buildartifact().get_media(buildId=build_id,
                                            target=target,
                                            attemptId=attempt_id,
                                            resourceId=resource_id)
  emu_filepath = EMULATOR_ZIP_DOWNLOAD_DIR + resource_id
  with io.FileIO(emu_filepath, mode='wb') as fh:
    downloader = abclient.apiclient.http.MediaIoBaseDownload(fh, req)
    done = False
    while not done:
      status, done = downloader.next_chunk()
      sys.stdout.write('\rDownloading... %d%% complete' % int(status.progress() * 100))
      sys.stdout.flush()
    print '\nDownload complete. File at %s.' % (emu_filepath)
  return emu_filepath


def unzipArtifacts(zip_location):
  """
  Function to unzip the files in a zip file.
  Used to unzip the artifact file downloaded from 'downloadArtifact' step.

  :param zip_location: Location of the zip file we wish to unzip.
  :return: emu_dir.  The directory root of unzipped folder.
  """
  def extract_file( zf, info, extract_dir ):
    zf.extract( info.filename, path=extract_dir )
    out_path = os.path.join( extract_dir, info.filename )

    perm = info.external_attr >> 16L
    os.chmod( out_path, perm )
  current_dir = os.path.dirname(os.path.realpath(__file__))
  # Remove the file extension at the end of the filename for the local directory.
  emu_dir = os.path.splitext(os.path.join(current_dir, os.path.basename(zip_location)))[0]
  print 'Unpacking zip file into location %s' % (emu_dir)
  zip_ref = zipfile.ZipFile(zip_location, 'r')
  for info in zip_ref.infolist():
    extract_file(zip_ref, info, emu_dir)
  # Remove the downloaded zip file
  os.remove(zip_location)
  return emu_dir


def extract_file( zf, info, extract_dir ):
  """
  Extract a ZipObject from the passed in ZipFile object to specified directory.

  :param zf: ZipFile object.
  :param info: ZipObject we wish to extract from zf.
  :param extract_dir: Directory we wish to extract to.
  :return: None.
  """
  zf.extract( info.filename, path=extract_dir )
  out_path = os.path.join( extract_dir, info.filename )
  perm = info.external_attr >> 16L
  os.chmod( out_path, perm )
