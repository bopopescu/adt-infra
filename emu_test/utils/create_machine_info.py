""" This program will create a proper machines.json file for use with the
    buildbot_breakage_report_adt.py script.

    To use, pass the Buildbot builders.pyl file as a input to this script.
"""

import sys
import ast
import json

def main():
  if len(sys.argv) is not 2:
    print 'Usage:  create_machine_info.py builders.pyl'
    return 1
  try:
    with open(sys.argv[1]) as f:
      content =  f.read()
  except IOError as e:
    print 'Cannot file builders.pyl file.  Aborting.'
    return 1
  builders_dict = ast.literal_eval(content)
  master_info = {}
  for builder in builders_dict['builders'].keys():
    current_builder = builders_dict['builders'][builder]
    if current_builder['tag'] not in master_info.keys():
      master_info[current_builder['tag']] = {}
    for category in current_builder['categories']:
      if category in master_info[current_builder['tag']].keys():
        master_info[current_builder['tag']][category].append(builder)
      else:
        master_info[current_builder['tag']][category] = [builder,]
  try:
    with open('machine_info.json', 'w') as outfile:
      json.dump(master_info, outfile, indent=4)
  except IOError as e:
    print 'Error writing JSON information ot machine_info.json file.  Aborting.'
    return 1
  print 'File machine_info.json created in local directory.'
  return 0

if __name__ == '__main__':
  sys.exit(main())
