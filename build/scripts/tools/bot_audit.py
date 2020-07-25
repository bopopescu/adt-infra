#!/usr/bin/env python
# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Create a dictionary of all Android bots listed by botmap.py."""

import json
import argparse
import os
import re
import sys


class Main:
  def __init__(self, name, bots=None, subordinates=None, is_internal=None):
    self.name = name
    self.is_internal = is_internal
    self.bots = bots
    self.subordinates = subordinates

  def __str__(self):
    if self.is_internal:
      return '%s, %s, %s, %s' % (self.name, len(self.bots), len(self.subordinates),
                                 self.is_internal)
    else:
      return '%s, %s, %s' % (self.name, len(self.bots), len(self.subordinates))


class Bot:
  def __init__(self, name, main, subordinate_name, is_internal=None):
    self.name = name
    self.main = main
    self.subordinate_name = subordinate_name
    self.is_internal = is_internal

  def __str__(self):
    if self.is_internal:
      return '%s, %s, %s, %s' % (self.name, self.main, self.subordinate_name,
                                 self.is_internal)
    else:
      return '%s, %s, %s' % (self.name, self.main, self.subordinate_name)

def get_main_map(bots):
  main_map = {}
  for bot in bots:
    main_name = bot.main
    if main_name in main_map.keys():
      main_map[main_name].append(bot)
    else:
      main_map[main_name] = [bot]
  return main_map

def is_subordinate_vm(subordinate_name):
  # Currently I don't know a better way to tell if a bot is a vm.
  return subordinate_name.startswith('vm') or subordinate_name.startswith('subordinate') or \
    subordinate_name.startswith('skia-android') or subordinate_name.startswith('skiabot-')

def is_bot_internal(main_name, internal_mains, public_mains):
  if not internal_mains and not public_mains:
    return None
  elif not internal_mains:
    return main_name not in public_mains
  elif not public_mains:
    return main_name in internal_mains
  elif main_name in internal_mains and main_name not in public_mains:
    return True
  elif main_name in public_mains and main_name not in internal_mains:
    return False
  else:
    print 'Warning: %s in bot internal and public main list' % main_name
    return None

def read_main_list(mains_list_file):
  mains = set()
  with open(mains_list_file, 'r') as f:
    main_lines = f.readlines()
    for main_name in main_lines:
      mains.add(main_name.strip())
  return mains

def main():
  parser = argparse.ArgumentParser(
    description='Given a file dump of botmap.py, audits the bots.')
  parser.add_argument('--bots-file', type=str,
                      help='File including dump of botmap.py')
  parser.add_argument('--internal-mains', type=str,
                      help='File that lists the internal mains.')
  parser.add_argument('--public-mains', type=str,
                      help='File that lists the public mains.')
  args = parser.parse_args()
  if not args.bots_file:
    print 'Need to pass --bots-file with list of bots.'
    return 1

  if args.internal_mains:
    internal_mains = read_main_list(args.internal_mains)
  else:
    internal_mains = None
  if args.public_mains:
    public_mains = read_main_list(args.public_mains)
  else:
    public_mains = None

  if not internal_mains and not public_mains:
    print ('Warning: Did not provide internal/public file(s). '
           'Unable to determine if bots are public or internal.')

  bot_lines = []
  with open(args.bots_file, 'r') as f:
    bot_lines = f.readlines()

  internal_bots = []
  public_bots = []
  for bot_line in bot_lines:
    bot_fields = bot_line.split()
    bot_fields = bot_fields[:len(bot_fields)-1]
    bot_name = ' '.join(bot_fields[3:])
    main_name = bot_fields[2]
    is_internal = is_bot_internal(main_name, internal_mains, public_mains)
    if is_internal is None:
      print 'WARNING: Can not process %s, because no internal/public bot info.' \
        % bot_name
    elif is_internal:
      internal_bots.append(Bot(bot_name, main_name, bot_fields[0],
                               is_internal))
    else:
      public_bots.append(Bot(bot_name, main_name, bot_fields[0],
                               is_internal))

  internal_main_map = get_main_map(internal_bots)
  public_main_map = get_main_map(public_bots)

  print 'main_name, # Bare-metal subordinates, # VMs'
  print 'Internal bots:'
  for main_name in internal_main_map.keys():
    # print '%s: %s' % (main_name, internal_main_map[main_name])
    internal_bots = internal_main_map[main_name]
    subordinate_set = set([bot.subordinate_name for bot in internal_bots])
    bare_metal_subordinates = [s for s in subordinate_set if not is_subordinate_vm(s)]
    vm_subordinates = [s for s in subordinate_set if is_subordinate_vm(s)]
    print '%s, %s, %s' % (main_name, len(bare_metal_subordinates), len(vm_subordinates))
    # for subordinate in sorted(subordinate_set):
    #   print '\t%s: bare-metal=%s' % (subordinate, subordinate in bare_metal_subordinates)

    
  print 'External bots:'
  for main_name in public_main_map.keys():
    # print '%s: %s' % (main_name, public_main_map[main_name])
    public_bots = public_main_map[main_name]
    subordinate_set = set([bot.subordinate_name for bot in public_bots])
    bare_metal_subordinates = [s for s in subordinate_set if not is_subordinate_vm(s)]
    vm_subordinates = [s for s in subordinate_set if is_subordinate_vm(s)]
    print '%s, %s, %s' % (main_name, len(bare_metal_subordinates), len(vm_subordinates))
    # for subordinate in sorted(subordinate_set):
    #   print '\t%s: bare-metal=%s' % (subordinate, subordinate in bare_metal_subordinates)

  # trybots = public_main_map['main.tryserver.chromium.linux']
  # for bot in trybots:
  #   print bot


if __name__ == '__main__':
  sys.exit(main())
