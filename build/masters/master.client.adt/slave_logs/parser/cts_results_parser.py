#!/usr/bin/python

import xml.etree.ElementTree as ET


_NAME_KEYS = (
        'PackageName', 'AppPackageName',
        'TestSuiteName',
        'TestCaseName',
        'TestName',
)
_ALL_KEYS = _NAME_KEYS + (
        'BuildId', 'BuildDate',
        'ABI',
        'Result',
)


def _insert_row(result, row):
    result.append(row)


def _extract_test(test, row, result):
    row['TestName'] = test.attrib.get('name', '')
    row['Result'] = test.attrib.get('result', '')
    _insert_row(result, row)


def _extract_test_case(testCase, row, result):
    row['TestCaseName'] = testCase.attrib.get('name', '')
    for test in [x for x in testCase if x.tag == 'Test']:
        _extract_test(test, dict(row), result)


def _extract_suite(suite, row, result):
    if row['TestSuiteName'] != '':
        row['TestSuiteName'] += '.'
    row['TestSuiteName'] += suite.attrib.get('name', '__')
    # Order of these for-loops is significant
    for testCase in [x for x in suite if x.tag == 'TestCase']:
        _extract_test_case(testCase, dict(row), result)
    for child in [x for x in suite if x.tag == 'TestSuite']:
        _extract_suite(child, dict(row), result)


def _extract_package(package, row, result):
    row['PackageName'] = package.attrib.get('name', '')
    row['AppPackageName'] = package.attrib.get('appPackageName', '')
    row['ABI'] = package.attrib.get('abi', '')
    row['TestSuiteName'] = ''
    for suite in [x for x in package if x.tag == 'TestSuite']:
        _extract_suite(suite, dict(row), result)


def extract_results(cts_file):
    """Parse a testResult.xml.

    Args:
        cts_file: Path to file to parse / open file handle for reading.

    Returns: list of dicts. Each dict has keys from |_ALL_KEYS|.
    """
    result = []
    tree = ET.parse(cts_file)
    root = tree.getroot()
    for package in root.findall('TestPackage'):
        _extract_package(package, {}, result)
    return result


def format_full_name(result):
    """Given a single result dict with keys in |_ALL_KEYS|, format the
       cannonical fullName."""
    return '/'.join([result.get(x, 'UNKNOWN') for x in _NAME_KEYS])
