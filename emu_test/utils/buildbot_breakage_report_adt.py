"""Downloads a json of builds for the builder and finds breakages.

   This script will query the BuildBot main for ADT (given a set of user
   inputs) and output the failure information it detects via the Buildbot
   JSON api.

   This script depends upon a file (default name machine_info.json) that
   contains information about the current setup of the Buildbot machines.
   This machine_info.json file can be generated by the script
   'create_machine_info.py' that is distributed with this script.
"""

import argparse
import json
import subprocess
import sys
import urllib2

from operator import attrgetter

URL_PREFIX = 'http://xinchan-lab2.mtv.corp.google.com:8700'
STRIP_UBERPROXY_PREFIX = 'https://goto.corp.google.com/adt-builder'
JSON_PREFIX = '%s/json/builders' % URL_PREFIX

# Utility class to allow shorthand usage of colored printing.
# To use, simply print out the class member you want before text,
# and terminate with ENDC to reset to default.
# For example:  print bcolors.WARNING + "Uhmmm..." + bcolors.ENDC
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# The normal (non error condition) recipe log identifiers
EXPECTED_RECIPE_LOGS = ['preamble', 'stdio', 'run_recipe', 'failure reason']

# The Families that are currently supported by ADT.
SUPPORTED_FAMILIES = ['ADB', 'CONSOLE', 'SYSTEM IMAGE RELEASE', 'UI',
                      'CROSS-BUILDS', 'EMU-2.2-RELEASE', 'EMU-MASTER-DEV',
                      'SYSTEM-IMAGE-BUILDS']

# The OS options that are currently supported by ADT.
SUPPORTED_OS = ['WINDOWS', 'MAC', 'LINUX']



def do_family(options):
  try:
    with open ('machine_info.json', 'r') as machine_info_json:
      machine_info = json.load(machine_info_json)
  except IOError as e:
    print 'Unable to find machine_info.json file.  Exiting'
    return 1
  if options.os not in machine_info.keys():
    print 'Operating System not found in machine_info file.  Exiting.'
    return 1
  if options.builder_family not in machine_info[options.os].keys():
    print 'Builder Family not found in machine_info file.  Exiting.'
    return 1
  for machine in machine_info[options.os][options.builder_family]:
    builder_name = machine.replace(" ", "%20") + '_%s' % (options.builder_family)
    build_range = range(-1, int(options.num_builds)*-1, -1)
    range_str = [str(x) for x in build_range]
    select_str = 'select=%s' % ('&select='.join(range_str))
    json_url_query = '%s/%s/builds?%s' % (JSON_PREFIX, builder_name, select_str)
    response = urllib2.urlopen(json_url_query)
    builds_json = json.loads(response.read())
    for x in builds_json:
      build_num = builds_json[x]['number']
      builds_json[str(build_num)] = builds_json.pop(x)
    print bcolors.BOLD + bcolors.HEADER + 'Failure information for Machine: %s' % (machine) + bcolors.ENDC
    parse_results(builds_json)


# If num_builds is specificed (ie not 0), then we ignore from_build and to_build
# variables and simply print the last num_builds builds.
def do_machine(options):
  builder_name = options.machine_name.replace(" ", "%20")

  # Use the options to create a buildbot json query and download json.
  build_range = range(int(options.from_build), int(options.to_build)+1)
  range_str = [str(x) for x in build_range]
  select_str = 'select=%s' % ('&select='.join(range_str))
  json_url_query = '%s/%s/builds?%s' % (JSON_PREFIX, builder_name, select_str)
  response = urllib2.urlopen(json_url_query)
  builds_json = json.loads(response.read())
  print bcolors.BOLD + bcolors.OKBLUE + 'Failure information for Machine: %s' % (options.machine_name) + bcolors.ENDC
  return parse_results(builds_json)


def parse_results(builds_json):
  # Analyze the downloaded json and come up with breakages.
  breakages = []
  cur_breakage = None
  trim_index = len('@google.com') * -1 # to trim @google.com from blamelists
  # There can be a wierd output occasionally that simply says 'error' with no index.
  # We are just pruning this possible output there (its useless to us anyway).
  for build in builds_json.values():
    if 'error' in build.keys():
      builds_json.pop(build)
  build_nums = [build['number'] for build in builds_json.values()]
  for build_num in sorted(build_nums):
    build = builds_json[str(build_num)]
    # A breakage is defined as consecutive red builds for the same reason.
    if build['results'] != 0:
      error_output = []
      for step in build['steps']:
        for log in step['logs']:
          if log[0] not in EXPECTED_RECIPE_LOGS:
            error_output.append(log[0])
      # Breakage found. Extract data regarding breakage from json.
      breakage_reason = error_output
      build_num = build['number']
      if cur_breakage and breakage_reason == cur_breakage['reason']:
        build_range = cur_breakage['build_range']
        cur_breakage['build_range'] = (build_range[0], build_num)
      else:
        cur_breakage = {}
        cur_breakage['build_range'] = (build_num, build_num)
        cur_breakage['reason'] = breakage_reason
        cur_breakage['blame'] = [blame[0:trim_index] if blame.endswith('@google.com')
                                                     else blame
                                                     for blame in build['blame']]
        cur_breakage['builder_name'] = build['builderName']
        breakages.append(cur_breakage)
    elif cur_breakage:
      # Green build after a breakage. See who fixed it.
      cur_breakage['fix'] = [blame[0:trim_index] if blame.endswith('@google.com') else blame
                                                 for blame in build['blame']]
      cur_breakage = None

  # Print the breakages into a csv breakage report.
  # print 'from, to, reason, blame, fix, link'
  if len(breakages) <= 0:
    print bcolors.OKGREEN + 'No Failures Detected on Machine' + bcolors.ENDC
    print ''
  else:
    print bcolors.FAIL + bcolors.BOLD + 'Failures Found on Machine' + bcolors.ENDC
    for breakage in breakages:
      build_range = breakage['build_range']
      link = '%s/builders/%s/builds/%s' % (URL_PREFIX,
                                           breakage['builder_name'].replace(" ", "%20"),
                                           build_range[0])
      blame = ':'.join(breakage['blame'])
      print bcolors.WARNING + '   Build Range of Failure: ' + bcolors.ENDC + '%s:%s' % (build_range[0], build_range[1])
      print bcolors.WARNING + '   Breakage Reason: ' + bcolors.ENDC + '%s' % (breakage['reason']) + bcolors.ENDC
      print bcolors.WARNING + '   link: ' + bcolors.UNDERLINE + bcolors.OKBLUE + '%s' % (link) + bcolors.ENDC
      print ''
  return



def main():
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(help='sub-command help', dest='command')
  # This set of options are part of group 'A'.  All are required within this group when executing a
  # 'A' request.
  parser_a = subparsers.add_parser('family', help='Examine the last N builds on a particular family-os combination')
  parser_a.add_argument('--machine_info', help='JSON file containing machine information.  Can be generated from the main builders.pyl '
                                               'with the "create_machine_info" script.  Argument not needed if file is in local directory.')
  parser_a.add_argument('--builder_family', help='The builder family (such as "emu-2.2-release")', required=True)
  parser_a.add_argument('--os', help='The Operating System for the given builder-family', required=True)
  parser_a.add_argument('--num_builds', help='The number of builds to look back on each builder', default=10)
  # This set of options are part of group 'B'.  All are required within this group when executing a
  # 'B' request.
  parser_b = subparsers.add_parser('machine', help='Examine failures on a particular machine between build numbers')
  parser_b.add_argument('--machine_name', help='The Particular Machine (ie "Ubuntu 12.04 HD Graphics 4000_emu-main-dev")', required=True)
  parser_b.add_argument('--from_build', help='The build number to start at.', required=True)
  parser_b.add_argument('--to_build', help='The build number to end at (inclusively).', required=True)
  options = parser.parse_args()
  if 'machine' in options.command:
    rc = do_machine(options)
  elif 'family' in options.command:
    rc = do_family(options)
  else:
    print 'Unknown command passed'


if __name__ == '__main__':
  sys.exit(main())
