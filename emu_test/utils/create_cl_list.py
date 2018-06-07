import os
import argparse
import subprocess
import psutil
import shutil
from android_cl_scan import query_ab


parser = argparse.ArgumentParser(description='Create a list of CL\'s for the passed in project between the two passed in build numbers.')
parser.add_argument('--poller', action='store',
                    help='String of the adt poller that initiated the build.')
parser.add_argument('--curRevision', action='store',
                    help='The Current revision (start point)')
parser.add_argument('--prevRevision', action='store',
                    help='The Previous revision (stop point).')
args = parser.parse_args()


def create_cl_list():
  '''Create a list of Changes for the passed in argument combination

  Returns Nothing.  Prints out output to stdout, which is captured by buildbot.

  Args:
    Depends upon argparse variables poller, curRevision and prevRevision.

  Returns:
    Nothing.  Prints out results to stdout, which is captured by buildbot in recipe stdout.
  '''
  print 'Calling into query_ab with: %s, %s, %s' % (args.poller, args.prevRevision, args.curRevision)
  changeSets = query_ab(args.poller, args.prevRevision, args.curRevision)
  print 'Changes included in this build:'
  print ''
  for change in changeSets:
    print 'CL %s' % (change['changeNumber'])
    print 'https://android-review.googlesource.com/#/c/%s' % (change['changeNumber'])
    print 'Owner: %s   in build: %s' % (change['email'], change['buildId'])
    print change['subject']
    print ''
  return 0


if __name__ == '__main__':
  exit(create_cl_list())
