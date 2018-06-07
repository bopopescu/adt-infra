# Copyright 2016 The Android Open Source Project
#
# This software is licensed under the terms of the GNU General Public
# License version 2, as published by the Free Software Foundation, and
# may be copied, distributed, and modified under those terms.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""Python objects to work with BigQuery table rows.

- Provides an append only 'table' object that is backed by a CSV/JSON file on
  disk. This file is accepted by the BigQuery API for table append operations.
- This object decides how often to flush the file to balance disk io vs memory
  usage.
- Does basic validity checking in case of FORMAT_CSV. In particular, the
  information about ordering of fields only kept in one place -- in the schema
  file.
"""

import json
import os
import os.path


class BigQueryTableException(Exception):
    """Any specific error raised from the BigQueryTable module"""


class GenericBigQueryTable(object):
    """A generic object to store a BigQuery table.

    You should use a subclass that is specialized to a fixed schema.

    NOTE: Always flush() the object at the end to ensure all data is written to
    disk.
    """

    # Subclasses must define a class variable SCHEMA_PATH pointing to the schema
    # to use.

    # Backing data formats.
    FORMAT_CSV = 'CSV'
    FORMAT_NEWLINE_DELIMITED_JSON = 'NEWLINE_DELIMITED_JSON'

    # Some useful schema keys and 'enum' values.
    # Always comapre ignoring case: my_string.lower() == SCHEMA_CONSTANT
    # XXX: lower() is not always correct for unicode.
    SCHEMA_KEY_TYPE = 'type'
    SCHEMA_KEY_NAME = 'name'
    SCHEMA_VALUE_TYPE_RECORD = 'record'

    # Control how many table entries can be kept in memory at any time.
    # This is a poor man's way to control the size of the data streaming
    # request. Subclass may override this.
    MAX_OUTSTANDING_LINES = 10000

    def __init__(self, out_file_dir, source_format):
        """Args:
            out_file_dir: Path prefix to the file where data for this table
                    should be written to. This should be a directory that
                    exists. Multiple files may be created inside it for the
                    data.
            source_format: The format in which backing data should be stored.
                    Options: FORMAT_CSV and FORMAT_NEWLINE_DELIMITED_JSON.
        """
        assert(self.SCHEMA_PATH)
        self._schema_file_path = self.SCHEMA_PATH
        self._source_format = source_format
        if source_format not in [self.FORMAT_CSV,
                                 self.FORMAT_NEWLINE_DELIMITED_JSON]:
            raise BigQueryTableException('Unrecoginzed source format: %s' %
                                         self._source_format)
        self._out_file_dir = out_file_dir
        self._out_file_num = 0
        self._out_files = []

        # Stores the data that is yet to be written to disk.
        # A list of rows. The way we store each row depends on |source_format|.
        # For FORMAT_CSV, each row is a list of items. For
        # FORMAT_NEWLINE_DELIMITED_JSON, each row is a (nested) dict that can be
        # dumped directly using json.dump
        self._table_suffix = []
        self._table_suffix_len = 0

        try:
            with open(self._schema_file_path, 'r') as f:
                self._schema = json.load(f)
        except ValueError as e:
            raise BigQueryTableException(
                    'Failed to load schema from |%s|: %s' %
                    (self._schema_file_path, str(e)))
        if not self._schema:
            raise BigQueryTableException('Loaded empty schema from |%s|' %
                                         self._schema_file_path)

        self._keys = []
        if self._source_format == self.FORMAT_CSV:
            try:
                self._extract_keys()
            except (KeyError, ValueError) as e:
                raise BigQueryTableException(
                        'Failed to extract keys from schema: %s' % str(e))

        # Create an empty backing file to make sure we can write to the path.
        try:
            os.mkdir(out_file_dir)
        except OSError:
            # Directory exists.
            pass
        try:
            out_file_path = self._current_file()
            with open(out_file_path, 'w') as f:
                f.flush()
        except IOError as e:
            raise BigQueryTableException(
                    'Failed to write backing file |%s|: %s' %
                    (out_file_path, str(e)))

    def append_row(self, row):
        """Append |row| to the table.

        Args:
            row: A (possibly nested) dict. Keys are names of columns in the
                    tables. Use nested dicts for specifying nested records in
                    the table. Non-existent keys / None values are dropped.
        """
        if self._source_format == self.FORMAT_NEWLINE_DELIMITED_JSON:
            # No validation.
            self._table_suffix.append(dict(row))
        elif self._source_format == self.FORMAT_CSV:
            formatted_row = []
            for key in self._keys:
                value = row.get(key, '')
                if value is not None:
                    formatted_row.append(value)
                else:
                    formatted_row.append('')
            self._table_suffix.append(formatted_row)
        else:
            assert False, ('Unreachable: Unknown source_format %s' %
                           self._source_format)
        self._maybe_write_to_disk()

    def flush(self):
        """Forcibly write all outstanding data to disk"""
        self._maybe_write_to_disk(forced=True)

    @property
    def source_format(self):
        return self._source_format

    @property
    def schema_path(self):
        return self._schema_file_path

    @property
    def backing_files(self):
        """Returns the list of files backing this table."""
        return self._out_files

    def _extract_keys(self):
        for item in self._schema:
            if (item[self.SCHEMA_KEY_TYPE].lower() ==
                self.SCHEMA_VALUE_TYPE_RECORD):
                raise BigQueryTableException(
                        'FORMAT_CSV does not support nested records')
            self._keys.append(item[self.SCHEMA_KEY_NAME])

    def _maybe_write_to_disk(self, forced=False):
        # Don't use len(self._table_suffix) because that's very costly to
        # compute on every append_row.
        self._table_suffix_len += 1
        if forced or self._table_suffix_len >= self.MAX_OUTSTANDING_LINES:
            try:
                self._write_to_disk()
            except (ValueError, IOError) as e:
                raise BigQueryTableException(
                        'Failed to flush table to disk: %s' % str(e))
            self._table_suffix_len = 0

    def _write_to_disk(self):
        out_file_path = self._current_file()
        with open(out_file_path, 'w') as outfile:
            for row in self._table_suffix:
                if self._source_format == self.FORMAT_NEWLINE_DELIMITED_JSON:
                    formatted_row = json.dumps(row)
                else:
                    # join doesn't like non strings in there.
                    row = [str(x) for x in row]
                    formatted_row = ','.join(row)
                outfile.write('%s%s' % (formatted_row, os.linesep))
            outfile.flush()
        self._table_suffix = []
        self._out_files.append(out_file_path)
        self._out_file_num += 1

    def _current_file(self):
        ext = '.csv' if self._source_format == self.FORMAT_CSV else '.json'
        return os.path.join(self._out_file_dir,
                            ('data' + str(self._out_file_num) + ext))


_BQ_SCHEMAS_DIR = 'bq_schemas'


class BootTimeTable(GenericBigQueryTable):
    """A BigQuery table that stores boot time data"""

    SCHEMA_PATH = os.path.join(_BQ_SCHEMAS_DIR, 'boot_time.json'),

    def __init__(self, out_file_dir):
        super(BootTimeTable, self).__init__(out_file_dir, self.FORMAT_CSV)


class AdbSpeedTable(GenericBigQueryTable):
    """A BigQuery table that stores boot time data"""

    SCHEMA_PATH = os.path.join(_BQ_SCHEMAS_DIR, 'adb_speed.json'),

    def __init__(self, out_file_dir):
        super(AdbSpeedTable, self).__init__(out_file_dir, self.FORMAT_CSV)


class CTSRawRun(GenericBigQueryTable):
    """A BigQuery table that summarizes results for each CTS run."""

    SCHEMA_PATH = os.path.join(_BQ_SCHEMAS_DIR, 'cts_raw_run.json'),

    def __init__(self, out_file_dir):
        super(CTSRawRun, self).__init__(out_file_dir, self.FORMAT_CSV)


class CTSRawResults(GenericBigQueryTable):
    """A BigQuery table that summarizes results for each CTS run."""

    SCHEMA_PATH = os.path.join(_BQ_SCHEMAS_DIR, 'cts_raw_results.json'),

    def __init__(self, out_file_dir):
        super(CTSRawResults, self).__init__(out_file_dir, self.FORMAT_CSV)


class PipelineSteps(GenericBigQueryTable):
    """The table that keeps tracks of in-flight pipeline steps."""

    SCHEMA_PATH = os.path.join(_BQ_SCHEMAS_DIR, 'pipeline_steps.json')

    def __init__(self, out_file_dir):
        super(PipelineSteps, self).__init__(out_file_dir, self.FORMAT_CSV)
