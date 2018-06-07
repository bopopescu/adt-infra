#!/usr/bin/python
"""Merges a set of test_result.xml files together such that:

  - a failure will be overwritten by a pass if one of the testcases has a pass
  - all test cases for which we have an exemption will be marked as a pass
  - removes all stacktraces of successful runs

   Note:

   - Running this can be very dangerous as no checks are made that the build type
   of the various xml files are actually matching. So be careful! You could easily merge
   two files whioch have different suite_versions etc!
   - Merging is reflexive. i.e. merge_result(a, b) == merge_result(b, a)


   The basic approach is pretty simple given two xml tree's A & B we do the following:

   merge_tree(a, b):
     merge_attributes_of(a, b)
     for every child in a and b:
       merge_tree(child_a, matching_child_in_b)

   Children that are in one tree but not another will be added.

   After the merge we apply the visitor pattern to:
     - update pass and failure count
     - mark exemptions as passing
     - remove stacktraces etc from successful nodes.

"""
from __future__ import print_function
from copy import copy
from lxml import etree
import argparse
import logging
import sys

# List of exemptions
thismodule = sys.modules[__name__]
thismodule.exemptions = frozenset()

def check_tag(left, right, tag):
  """Checks to see if the tags are of the same type"""
  if (left.tag != tag or right.tag != tag):
    raise Exception("Nodes are not of right tag! left: {0}, rigth: {1}, tag: {2}".format(left, right, tag))

def merge_attributes(left, right, resolve):
  """Merges a dictionary of attributes using the given resolve strategy.

     The resolve strategy will be invoked if the key exists in both dictionaries
     but do not have the same value.
  """
  merged = {}
  for key in left:
    # Both in left & right
    if key in right:
      # 2 cases. they are the same, we are good. otherwise resolve the
      # conflict.
      if left[key] == right[key]: merged[key] = left[key]
      else: merged[key] = resolve(key,left[key], right[key])
    else:
      # Only in the left..
      merged[key] = left[key]

  # Handle those that were left-ver
  for key in right:
    if not key in left: merged[key] = right[key]

  logging.debug('merge_attributes: {0} + {1} = {2}'.format(left, right, merged))
  return merged


def zipr(left, right, node_key, merge_function):
  """Zips a left and right tree

     The children are zipped in the order as declared by the node_key function.
     The merge function is called for each node that needs to be merged.

     You very likely want this function to recurse down :-)
  """
  left_sorted = sorted(left, key=node_key)
  right_sorted = sorted(right, key=node_key)
  merged = []
  l, r = 0, 0
  while(l < len(left_sorted) or r < len(right_sorted)):
    left_key = node_key(left_sorted[l]) if (l < len(left_sorted)) else  None
    right_key = node_key(right_sorted[r]) if (r < len(right_sorted)) else None
    if (left_key != None and left_key < right_key) or right_key == None:
    # take left while l.tag < r.tag (Note: None is minimal element)
      merged.append(copy(left_sorted[l]))
      l = l + 1
    elif (right_key != None and right_key < left_key) or left_key == None:
      # take right while r.tag < l.tag, or we are done with the left tags
      merged.append(copy(right_sorted[r]))
      r = r+ 1
    else:
      # tag left == tag right.. we actually need to merge
      merged.append(merge_function(left_sorted[l], right_sorted[r]))
      l = l + 1
      r = r + 1
  return merged

def merge_node(left, right, attrib_resolver):
  """Merges two XML trees"""
  logging.debug('merge_node {0} with: {1}'.format(left, right))

  if (left is None): return copy(right)
  if (right is None): return copy(left)

  # Make sure we are merging tags that are the same!
  check_tag(left, right, left.tag)

  new_node = etree.Element(left.tag)
  new_node.text = copy(left.text)

  # Merge all the attributes of this node.
  merged_attr = merge_attributes(left.attrib, right.attrib, attrib_resolver)
  for k, v in merged_attr.iteritems():
    new_node.attrib[k] = v

  # We recursively merge the tree by ordered by tag and name if available..
  sort_by_tag = lambda x: (x.tag  + "$#$" + str(x.get('name')))

  # We merge nodes by recursively going down..
  rec_merge = lambda l,r: merge_node(l, r, attrib_resolver)
  kids = zipr(left, right, sort_by_tag, rec_merge)
  for kid in kids: new_node.append(kid)

  return new_node


def pass_resolver(key, left, right):
  """A merge resolver that resolves result and done attributes properly.

     pass_resolver(key, a, b) == pass_resolver(key, b, a)
  """
  if key == 'result' and (left == 'pass' or right == 'pass'): return 'pass'
  if key == 'done' and (left == 'true' or right == 'true'): return 'true'
  res = min(left, right)
  if left != right: logging.debug("resolving {0}, mismatch {1}, {2}, using: {3}".format(key, left, right, res))
  return res

def visit(node, down, fn_up, fn_down):
  """A visitor that flows up all data from its children

  """
  ups = []
  down = fn_down(node, down)
  for child in node:
    ups.append(visit(child, down, fn_up, fn_down))
  return fn_up(node, ups)


def update_counters(node, ups):
  """
     A visitor function that will count all success and failures, updating
     tags as needed
  """
  up = {}
  logging.debug('updating {0} with: {1}'.format(node, ups))

  # Pull up success and failures counts
  if (node.tag =='Module' or node.tag == 'TestCase'):
    up['pass'] = reduce(lambda x, u: x + (u['pass'] if 'pass' in u else 0), ups, 0)
    up['fail'] = reduce(lambda x, u: x + (u['fail'] if 'fail' in u else 0), ups, 0)

    node.attrib['fail'] = str(up['fail'])
    node.attrib['pass'] = str(up['pass'])

  if (node.tag == 'Test'):
    # First filter out our exemptions.. We will mark it as a pass..
    testname = "{0}.{1}".format(node.get('name'), node.getparent().get('name'))
    if testname in thismodule.exemptions: node.attrib['result'] = 'pass'

    up[node.get('result')] = 1

    if node.get('result') == 'pass':
      # Remove stack traces from children.
      for child in node:
        node.remove(child)
  return up


def update_summary(tree):
  """Update the summary tag with the proper information"""
  summary = tree.xpath("/Result/Summary")[0]
  modules = tree.xpath("//Module")
  done    = len(tree.xpath("//Module[@done='true']"))
  success = reduce(lambda x, y: x + int(y.get("pass")), modules, 0)
  fail    = reduce(lambda x, y: x + int(y.get("fail")), modules, 0)

  summary.attrib["failed"] = str(fail)
  summary.attrib["pass"]   = str(success)
  summary.attrib["modules_total"] = str(len(modules))
  summary.attrib["modules_done"]  = str(done)
  logging.info("Summary: Total modules: {0}, done: {1}, passed tests: {2}, failed: {3}".format(
        len(modules), done, success, fail))

def filter_success(node):
  """Filters out all the passing results, leaving only failures in the tree"""
  for n in node:
    filter_success(n)

  if node.get("result") == "pass" or (node.get("result") is None and len(node) == 0):
    node.getparent().remove(node)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Merge and normalize a set of test_result.xml files. '
                                     'Bad files will not be merged in and will be skipped. '
                                     'An exit code of 0 means that the final result has no failures.'
                                     )
    parser.add_argument('-i', '--input', dest='inputs', nargs="+", type=str, required=True,
                        help='list of input xml files that should be merged and normalized')
    parser.add_argument('-o', '--output', dest='output',
                        help='output file to write the resulting xml to')
    parser.add_argument('-e', '--exclude_exemptions', dest='exempt',
                        help='Extract the list of exemptions from the given test_result.xml file. '
                        'Failures in this xml file will be marked as pass in the final result')
    parser.add_argument('-f', '--only-failures', dest='filter', action='store_true', 
                        help='Only keep the failures, remove all other nodes')
    parser.add_argument('-d', '--debug', action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.ERROR, help="Print lots of debugging statements")
    parser.add_argument('-v', '--verbose',
                        action="store_const", dest="loglevel", const=logging.INFO,
                        help="Be more verbose")
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    if args.output is None:
      target = sys.stdout
    else:
      target = open(args.output, 'w')
    if args.exempt is not None:
      l = etree.parse(args.exempt)
      thismodule.exemptions = frozenset(
          ["{0}.{1}".format(x.get('name'), x.getparent().get('name')) for x in l.xpath('//Test[@result="fail"]')]
      )

    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)

    tree = None
    for f in args.inputs:
      try:
        logging.info('Processing {0}'.format(f))
        root = etree.parse(f, parser).getroot()
        if tree is None: tree = root
        else: tree = merge_node(tree, root, pass_resolver)
      except Exception as e:
        logging.error("Failed to merge in {0} due to {1}".format(f, e))

    if tree is None:
      logging.error("No trees were merged.")
      exit(1)

    # Filter out all the success runs if desired
    if args.filter: map(lambda x: filter_success(x), tree.xpath('//Module'))

    # Visitor pattern to calculate pass/fail rate
    logging.info("Post processing counters, filtering: {0}".format(thismodule.exemptions))
    visit(tree, {},  update_counters, lambda x,y: y)

    # Re calculate the summary tag.
    update_summary(tree)

    tree.addprevious(etree.Comment("This file was generated by executing:\n\n {0}\n\n".format(" ".join(sys.argv))))
    tree = etree.ElementTree(tree)
    # write out the result
    target.write("<?xml version='1.0' encoding='UTF-8' standalone='no' ?>\n")
    target.write("<?xml-stylesheet type=\"text/xsl\" href=\"compatibility_result.xsl\"?>\n")
    target.write(etree.tostring(tree, xml_declaration=False, pretty_print=True))

    if target is not sys.stdout: target.close()

if __name__ == "__main__":
    sys.exit(main())
