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

import simple_parsers as sp

import collections
import json
import logging
import os
import pprint
import threading
import time
import uuid
from apiclient import http
from googleapiclient import discovery


class BigQueryException(Exception):
    """Any intelligible exception from this module."""

_Context = collections.namedtuple(
        '_Context',
        ['lock', 'bigquery', 'project_id', 'dataset_id', 'table_id',
         'data_format', 'schema_path'])
_UploadItem = collections.namedtuple(
        '_UploadItem',
        ['context', 'data_path'])


def _upload_one(item):
    """The engine behind |BigQuery.upload|.

    Args:
        item: An _UploadItem to upload.
    """
    context = item.context
    logging.debug('Uploading data to (project:%s, datatset:%s, table:%s) '
                  'from %s with schema %s' %
                  (context.project_id, context.dataset_id, context.table_id,
                   item.data_path, context.schema_path))
    size = os.stat(item.data_path).st_size
    if size == 0:
        logging.info('No data found. Skipping upload.')
        return
    if size > 10 * 1024 * 1024:
        logging.error('File to upload too large (%s MB). '
                      'BigQuery limit is 10 MB. Upload will likely fail.' %
                      (size,))

    # Post to the jobs resource using the client's media upload interface.
    # See:
    # http://developers.google.com/api-client-library/
    #         python/guide/media_upload

    # Provide a configuration object. See:
    # https://cloud.google.com/bigquery/docs/reference/v2/jobs#resource
    body = {
        'configuration': {
            'load': {
                'schema': {
                    'fields': json.load(open(context.schema_path, 'r'))
                },
                'destinationTable': {
                    'projectId': context.project_id,
                    'datasetId': context.dataset_id,
                    'tableId': context.table_id
                },
                'sourceFormat': context.data_format,
            }
        }
    }
    media_body = http.MediaFileUpload(
        item.data_path,
        mimetype='application/octet-stream')

    with context.lock:
        insert_request = context.bigquery.jobs().insert(
            projectId=context.project_id,
            body=body,
            media_body=media_body)
        job = insert_request.execute()
        status_request = context.bigquery.jobs().get(
            projectId=job['jobReference']['projectId'],
            jobId=job['jobReference']['jobId'])

    # Poll the job until it finishes.
    while True:
        with context.lock:
            result = status_request.execute(num_retries=2)

        status = result['status']
        if status['state'] != 'DONE':
            time.sleep(1)
            continue

        if 'errorResult' not in status:
            break

        msg = ('Error when updating table %s with rows from %s using '
               'schema %s' % (context.table_id, item.data_path,
                              context.schema_path))
        error = status['errorResult']
        if 'debugInfo' in error:
            del error['debugInfo']
        logging.error(pprint.pformat(error))
        raise BigQueryException(msg)


class BigQuery(object):
    """Client object to interact with a BigQuery dataset

    Default values are set for a test dataset. Bots should override this.
    """

    NUM_CONCURRENT_UPLOADS = 20
    QUERY_TEMPLATE_PARAMTER = 'DATASET_ID'
    DEFAULT_PROJECT_ID = 'android-devtools-emulator'
    DEFAULT_DATASET_ID = 'emu_buildbot_test'

    def __init__(self, project_id=None, dataset_id=None, credentials=None):
        assert credentials is not None
        if project_id is not None:
            self._project_id = project_id
        else:
            self._project_id = self.DEFAULT_PROJECT_ID
        if dataset_id is not None:
            self._dataset_id = dataset_id
        else:
            self._dataset_id = self.DEFAULT_DATASET_ID

        self._bigquery = discovery.build('bigquery', 'v2',
                                         credentials=credentials)

    @property
    def dataset(self):
        return self._dataset_id

    def upload(self, bq_table, table_id):
        """Uploads data from GenericBigQueryTable |bq_tale| to |table_id|.

        Skips empty files.
        """
        bq_table.flush()
        data_format = ('CSV' if bq_table.source_format == bq_table.FORMAT_CSV
                       else 'NEWLINE_DELIMITED_JSON')
        context = _Context(
                threading.Lock(), self._bigquery, self._project_id,
                self._dataset_id, table_id, data_format, bq_table.schema_path)
        items = [_UploadItem(context, x) for x in bq_table.backing_files]
        threads = [threading.Thread(target=_upload_one,
                                    args=(i,))
                   for i in items]
        done = 0
        while threads:
            concurrency = min(self.NUM_CONCURRENT_UPLOADS, len(threads))
            logging.info(
                    'Starting next batch of %d threads to upload files: %s' %
                    (concurrency,
                     [x.data_path for x in items[done:done+concurrency]]))
            for i in range(concurrency):
                threads[i].start()
            for i in range(concurrency):
                threads[i].join()
            threads = threads[concurrency:]
            done += concurrency
        logging.info('Upload complete.')

    def delete(self, table_name):
        """Deletes the specific table, synchronously."""
        self._bigquery.tables().delete(projectId=self._project_id,
                                       datasetId=self._dataset_id,
                                       tableId=table_name).execute()

    def batch_query(self, query_template, destination_table,
                    destination_dataset=None):
        """Run a query on bigquery in batch mode.

        Runs a query on bigquery in batch mode. The result of the query is
        written to |destination_table|.
        Query should be specified as a templated string where all occurences of
        DATASET_ID will be replaced with the current dataset id.

        If provided, |destination_table| will be created/appended to in the
        |destination_dataset|.
        """
        return self._run_async_query(
                self._format_query(query_template),
                destination_dataset=destination_dataset,
                destination_table=destination_table)

    def sync_query(self, query_template, return_table_schema, timeout_s=60):
        """Runs a synchronous query and returns the result.

        Args:
            query_template: A templated string where all occurences of
                    DATASET_ID will be replaced with the current dataset id.
            return_table_schema: A path to a schema file for the returned data,
                    or a list(dict) specifying the schema.
        Returns: A list of dicts, where each dict is one row of data:
                [{column_name: value}] with |value| in the correct python data
                type.
        """
        if isinstance(return_table_schema, str):
            with open(return_table_schema, 'r') as f:
                return_table_schema = json.load(f)

        query = self._format_query(query_template)
        logging.debug('Running (de-templated) query: |%s|', query)
        job_id = self._run_async_query(
                query, batch_mode=False, large_tables_mode=False)

        rows = []
        page_token = None
        while True:
            page = self._bigquery.jobs().getQueryResults(
                    projectId=self._project_id,
                    jobId=job_id,
                    pageToken=page_token,
                    timeoutMs=timeout_s*1000).execute(num_retries=2)
            # After the first query, we'll wait only 5 seconds for successive
            # results.
            timeout_s = 5

            if not page['jobComplete']:
                msg = ('Timed out waiting for query to complete: |%s|' %
                       (query,))
                logging.error(msg)
                raise BigQueryException(msg)

            rows += page['rows']
            page_token = page.get('pageToken')
            if page_token is None:
                break

        return self._marshall_query_result(rows, return_table_schema)

    def job_completed(self, job_id):
        """Check the status of the indicated job.

        Returns: True if the job completed successfully, False if it is still
                outstanding.
        Raises: BigQueryException if an error occured in running the job.
        """
        try:
            result = self._bigquery.jobs().get(
                projectId=self._project_id,
                jobId=job_id).execute(num_retries=2)
        except http.HttpError:
            raise BigQueryException('Job %s does not exist' % (job_id,))

        status = result['status']
        if status['state'] != 'DONE':
            return False
        if 'errorResult' not in status:
            return True

        error = status['errorResult']
        if 'debugInfo' in error:
            del error['debugInfo']
        logging.error('Job %s failed.', job_id)
        logging.error(pprint.pformat(error))
        raise BigQueryException('Job %s failed.' % (job_id,))

    def _run_async_query(self, query,
                         destination_dataset=None, destination_table=None,
                         batch_mode=True, large_tables_mode=True):
        job_id = str(uuid.uuid4())
        body = {
                'jobReference': {
                    'projectId': self._project_id,
                    'job_id': job_id
                },
                'configuration': {
                        'query': {
                                'query': query,
                                'priority': ('BATCH' if batch_mode
                                             else 'INTERACTIVE')
                        }
                }
        }
        query_config = body['configuration']['query']
        if destination_dataset is None:
            destination_dataset = self._dataset_id
        if destination_table is not None:
            query_config['destinationTable'] = {
                    'projectId': self._project_id,
                    'datasetId': destination_dataset,
                    'tableId': destination_table
            }
            query_config['createDisposition'] = 'CREATE_IF_NEEDED'
            query_config['writeDisposition'] = 'WRITE_APPEND'
        if large_tables_mode:
            body['configuration']['query']['allowLargeResults'] = True

        insert_request = self._bigquery.jobs().insert(
                projectId=self._project_id,
                body=body)
        return insert_request.execute(num_retries=2)['jobReference']['jobId']

    def _format_query(self, query_template):
        return query_template.replace(self.QUERY_TEMPLATE_PARAMTER,
                                      self._dataset_id).strip()

    def _marshall_query_result(self, result, schema):
        num_columns = len(schema)
        names = [x['name'] for x in schema]
        types = [x['type'].lower() for x in schema]
        allowed_types = set(['string', 'integer', 'float', 'timestamp'])
        contained_types = set([x for x in types])
        if contained_types - allowed_types:
            raise BigQueryException('Schema contains disallowed types: %s' %
                                    (str(contained_types - allowed_types),))

        marshalled = []
        for row in result:
            columns = row['f']
            if len(columns) != num_columns:
                raise ValueError('Row should have %d columns, has %d' %
                                 (num_columns, len(columns)))

            marshalled_row = {}
            for c in range(num_columns):
                value = columns[c]['v']
                if types[c] == 'integer':
                    value = int(value)
                elif types[c] == 'float':
                    value = float(value)
                elif types[c] == 'timestamp':
                    value = sp.bq_parse_timestamp(value)
                marshalled_row[names[c]] = value
            marshalled.append(marshalled_row)
        return marshalled
